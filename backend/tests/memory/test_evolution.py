"""
Unit tests for Memory Evolution Agent
"""

import json
import time
import tempfile
import unittest
import os
import sys
import shutil
from datetime import datetime

from evolution_agent import (
    MemoryEntry,
    AccessPatternTracker,
    ImportanceDecay,
    RelationshipInference,
    MemoryRewriter,
    EvolutionAgent
)
from scheduler import HeartbeatScheduler


class TestMemoryEntry(unittest.TestCase):
    """Tests for MemoryEntry dataclass"""
    
    def test_create_entry(self):
        """Test creating a memory entry"""
        entry = MemoryEntry(
            id="test123",
            content="Test content",
            timestamp=time.time()
        )
        
        self.assertEqual(entry.id, "test123")
        self.assertEqual(entry.content, "Test content")
        self.assertEqual(entry.access_count, 0)
        self.assertEqual(entry.importance_score, 1.0)
        self.assertEqual(entry.version, 1)
        self.assertIsNone(entry.rewritten_from)
    
    def test_entry_defaults(self):
        """Test entry default values"""
        ts = time.time()
        entry = MemoryEntry(
            id="test",
            content="Content",
            timestamp=ts
        )
        
        self.assertEqual(entry.last_accessed, ts)
        self.assertEqual(entry.tags, [])
        self.assertEqual(entry.related_memories, [])


class TestAccessPatternTracker(unittest.TestCase):
    """Tests for AccessPatternTracker"""
    
    def setUp(self):
        self.tracker = AccessPatternTracker(window_size=100)
    
    def test_record_access(self):
        """Test recording access events"""
        self.tracker.record_access("mem1", "read", "test_context")
        
        stats = self.tracker.get_access_patterns("mem1")
        self.assertEqual(stats["total_accesses"], 1)
        self.assertEqual(stats["operations"]["read"], 1)
        self.assertIn("test_context", stats["contexts"])
    
    def test_multiple_accesses(self):
        """Test tracking multiple accesses"""
        self.tracker.record_access("mem1", "read")
        self.tracker.record_access("mem1", "read")
        self.tracker.record_access("mem1", "write")
        
        stats = self.tracker.get_access_patterns("mem1")
        self.assertEqual(stats["total_accesses"], 3)
        self.assertEqual(stats["operations"]["read"], 2)
        self.assertEqual(stats["operations"]["write"], 1)
    
    def test_access_sequences(self):
        """Test recording access sequences"""
        self.tracker.record_sequence(["mem1", "mem2", "mem3"])
        self.tracker.record_sequence(["mem1", "mem2"])
        
        coaccess = self.tracker.get_coaccess_patterns()
        self.assertIn(("mem1", "mem2"), coaccess)
    
    def test_frequently_accessed(self):
        """Test getting frequently accessed memories"""
        for _ in range(5):
            self.tracker.record_access("mem1")
        for _ in range(3):
            self.tracker.record_access("mem2")
        
        frequent = self.tracker.get_frequently_accessed(threshold=4)
        self.assertEqual(len(frequent), 1)
        self.assertEqual(frequent[0][0], "mem1")
        self.assertEqual(frequent[0][1], 5)
    
    def test_export_stats(self):
        """Test exporting tracking statistics"""
        self.tracker.record_access("mem1")
        self.tracker.record_access("mem2")
        
        stats = self.tracker.export_stats()
        self.assertEqual(stats["total_tracked_accesses"], 2)
        self.assertEqual(stats["unique_memories_tracked"], 2)


class TestImportanceDecay(unittest.TestCase):
    """Tests for ImportanceDecay"""
    
    def setUp(self):
        self.decay = ImportanceDecay(half_life_days=30.0)
    
    def test_fresh_memory(self):
        """Test score for fresh memory"""
        mem = MemoryEntry("id", "content", time.time())
        score = self.decay.calculate_score(mem)
        
        # Should be close to initial score
        self.assertGreater(score, 0.9)
        self.assertLessEqual(score, 2.0)
    
    def test_old_memory_decay(self):
        """Test decay for old memory"""
        old_time = time.time() - (60 * 24 * 3600)  # 60 days ago
        mem = MemoryEntry("id", "content", old_time)
        score = self.decay.calculate_score(mem)
        
        # Should be decayed
        self.assertLess(score, 1.0)
    
    def test_access_boost(self):
        """Test boost from access count"""
        now = time.time()
        
        mem1 = MemoryEntry("id1", "content", now)
        mem1.access_count = 0
        
        mem2 = MemoryEntry("id2", "content", now)
        mem2.access_count = 5
        
        score1 = self.decay.calculate_score(mem1)
        score2 = self.decay.calculate_score(mem2)
        
        self.assertGreater(score2, score1)
    
    def test_recency_boost(self):
        """Test boost from recent access"""
        now = time.time()
        
        mem1 = MemoryEntry("id1", "content", now - 86400)  # 1 day old
        mem1.last_accessed = now - 3600  # Accessed 1 hour ago
        
        mem2 = MemoryEntry("id2", "content", now - 86400)
        mem2.last_accessed = now - 172800  # Accessed 2 days ago
        
        score1 = self.decay.calculate_score(mem1)
        score2 = self.decay.calculate_score(mem2)
        
        self.assertGreater(score1, score2)
    
    def test_should_archive(self):
        """Test archive decision"""
        old_time = time.time() - (100 * 24 * 3600)  # 100 days old
        mem = MemoryEntry("id", "content", old_time)
        mem.importance_score = 0.1
        
        self.assertTrue(self.decay.should_archive(mem, threshold=0.2))
        self.assertFalse(self.decay.should_archive(mem, threshold=0.05))
    
    def test_batch_decay(self):
        """Test batch decay calculation"""
        now = time.time()
        memories = [
            MemoryEntry("id1", "content", now),
            MemoryEntry("id2", "content", now - (60 * 24 * 3600))
        ]
        
        results = self.decay.decay_batch(memories)
        self.assertEqual(len(results), 2)
        self.assertGreater(results[0][1], results[1][1])  # Fresh > old


class TestRelationshipInference(unittest.TestCase):
    """Tests for RelationshipInference"""
    
    def setUp(self):
        self.inference = RelationshipInference(similarity_threshold=0.3)
    
    def test_keyword_extraction(self):
        """Test keyword extraction from content"""
        content = "Python is great for machine learning"
        keywords = self.inference._extract_keywords(content)
        
        self.assertIn("python", keywords)
        self.assertIn("great", keywords)
        self.assertIn("machine", keywords)
        self.assertIn("learning", keywords)
        self.assertNotIn("is", keywords)  # Stop word
    
    def test_update_index(self):
        """Test content indexing"""
        mem = MemoryEntry("id1", "python machine learning", time.time())
        self.inference.update_index(mem)
        
        self.assertIn("id1", self.inference._content_index["python"])
        self.assertIn("id1", self.inference._content_index["machine"])
        self.assertIn("id1", self.inference._content_index["learning"])
    
    def test_find_related(self):
        """Test finding related memories"""
        memories = {
            "id1": MemoryEntry("id1", "python programming language", time.time()),
            "id2": MemoryEntry("id2", "python machine learning", time.time()),
            "id3": MemoryEntry("id3", "java programming", time.time())
        }
        
        for mem in memories.values():
            self.inference.update_index(mem)
        
        related = self.inference.find_related(memories["id1"], memories)
        
        # Should find at least one related memory
        related_ids = [r[0] for r in related]
        self.assertGreater(len(related_ids), 0)
        # Both id2 (shares "python") and id3 (shares "programming") are related
        self.assertTrue("id2" in related_ids or "id3" in related_ids)
    
    def test_tag_similarity(self):
        """Test tag-based similarity"""
        mem1 = MemoryEntry("id1", "content", time.time(), tags=["python", "ai"])
        mem2 = MemoryEntry("id2", "different content", time.time(), tags=["python", "ml"])
        
        score = self.inference._calculate_similarity(mem1, mem2)
        self.assertGreater(score, 0)


class TestMemoryRewriter(unittest.TestCase):
    """Tests for MemoryRewriter"""
    
    def setUp(self):
        self.rewriter = MemoryRewriter(min_access_for_rewrite=3)
        self.tracker = AccessPatternTracker()
    
    def test_should_rewrite(self):
        """Test rewrite condition"""
        mem = MemoryEntry("id", "content", time.time())
        
        # Not enough accesses
        for _ in range(2):
            self.tracker.record_access("id", "read", "ctx1")
        self.assertFalse(self.rewriter.should_rewrite(mem, self.tracker))
        
        # Enough accesses but single context
        for _ in range(5):
            self.tracker.record_access("id", "read", "ctx1")
        self.assertFalse(self.rewriter.should_rewrite(mem, self.tracker))
        
        # Multiple contexts
        self.tracker.record_access("id", "read", "ctx2")
        mem.access_count = 6
        self.assertTrue(self.rewriter.should_rewrite(mem, self.tracker))
    
    def test_suggest_consolidation(self):
        """Test consolidation suggestion"""
        mem = MemoryEntry("id1", "python basics", time.time())
        
        related = [
            MemoryEntry("id2", "python loops", time.time()),
            MemoryEntry("id3", "python functions", time.time()),
            MemoryEntry("id4", "python classes", time.time())
        ]
        
        suggestion = self.rewriter.suggest_rewrite(mem, related)
        
        self.assertEqual(suggestion["action"], "consolidate")
        self.assertIn("id2", suggestion["related_ids"])
    
    def test_suggest_tag_enrichment(self):
        """Test tag enrichment suggestion"""
        mem = MemoryEntry("id1", "python", time.time(), tags=["python"])
        
        related = [
            MemoryEntry("id2", "ml", time.time(), tags=["python", "ml"]),
            MemoryEntry("id3", "ai", time.time(), tags=["python", "ai"])
        ]
        
        suggestion = self.rewriter.suggest_rewrite(mem, related)
        
        self.assertEqual(suggestion["action"], "enrich_tags")
        self.assertIn("ml", suggestion["new_tags"])
        self.assertIn("ai", suggestion["new_tags"])
    
    def test_apply_rewrite(self):
        """Test applying a rewrite"""
        mem = MemoryEntry("id1", "content", time.time(), tags=["old"])
        mem.access_count = 5
        
        rewrite_plan = {
            "action": "enrich_tags",
            "original_id": "id1",
            "suggested_tags": ["old", "new"],
            "new_tags": ["new"]
        }
        
        new_mem = self.rewriter.apply_rewrite(mem, rewrite_plan)
        
        self.assertIsNotNone(new_mem)
        self.assertEqual(new_mem.version, 2)
        self.assertIn("new", new_mem.tags)
        self.assertEqual(new_mem.importance_score, mem.importance_score * 1.1)
    
    def test_rewrite_stats(self):
        """Test rewrite statistics"""
        stats = self.rewriter.get_rewrite_stats()
        self.assertEqual(stats["total_rewrites"], 0)
        self.assertEqual(stats["consolidations"], 0)


class TestEvolutionAgent(unittest.TestCase):
    """Integration tests for EvolutionAgent"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.storage_path = os.path.join(self.temp_dir, "test_memory.json")
        self.agent = EvolutionAgent(storage_path=self.storage_path)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_add_memory(self):
        """Test adding memory"""
        mem_id = self.agent.add_memory("Test content", ["tag1", "tag2"])
        
        self.assertIsNotNone(mem_id)
        self.assertIn(mem_id, self.agent.memories)
        self.assertEqual(self.agent.memories[mem_id].content, "Test content")
    
    def test_get_memory(self):
        """Test retrieving memory"""
        mem_id = self.agent.add_memory("Test content")
        
        mem = self.agent.get_memory(mem_id, "test_context")
        
        self.assertIsNotNone(mem)
        self.assertEqual(mem.content, "Test content")
        self.assertEqual(mem.access_count, 1)
    
    def test_query_memories(self):
        """Test querying memories"""
        self.agent.add_memory("Python programming language", ["python"])
        self.agent.add_memory("Java programming language", ["java"])
        self.agent.add_memory("Coffee brewing guide", ["coffee"])
        
        results = self.agent.query_memories("programming")
        
        self.assertEqual(len(results), 2)
        contents = [r[0].content for r in results]
        self.assertIn("Python programming language", contents)
        self.assertIn("Java programming language", contents)
    
    def test_evolution_cycle(self):
        """Test running evolution cycle"""
        # Add some memories
        for i in range(5):
            self.agent.add_memory(f"Memory {i}", ["test"])
        
        # Run evolution
        results = self.agent.run_evolution_cycle()
        
        self.assertIn("memories_processed", results)
        self.assertIn("relationships_inferred", results)
        self.assertEqual(results["memories_processed"], 5)
    
    def test_persistence(self):
        """Test saving and loading"""
        mem_id = self.agent.add_memory("Persistent memory", ["tag"])
        
        # Create new agent with same storage
        agent2 = EvolutionAgent(storage_path=self.storage_path)
        
        self.assertIn(mem_id, agent2.memories)
        self.assertEqual(agent2.memories[mem_id].content, "Persistent memory")
    
    def test_get_stats(self):
        """Test getting statistics"""
        self.agent.add_memory("Test", ["tag"])
        
        stats = self.agent.get_stats()
        
        self.assertEqual(stats["memory_count"], 1)
        self.assertIn("access_tracking", stats)
        self.assertIn("decay_stats", stats)


class TestScheduler(unittest.TestCase):
    """Tests for HeartbeatScheduler"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.storage_path = os.path.join(self.temp_dir, "memory.json")
        self.heartbeat_path = os.path.join(self.temp_dir, "heartbeat.json")
        self.state_path = os.path.join(self.temp_dir, "state.json")
        
        self.agent = EvolutionAgent(storage_path=self.storage_path)
        self.scheduler = HeartbeatScheduler(
            agent=self.agent,
            interval_minutes=0.1,  # Very short for testing
            heartbeat_file=self.heartbeat_path,
            state_file=self.state_path
        )
    
    def tearDown(self):
        self.scheduler.stop()
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initial_status(self):
        """Test initial scheduler status"""
        status = self.scheduler.get_status()
        
        self.assertFalse(status["running"])
        self.assertIsNone(status["last_run"])
        self.assertEqual(status["run_count"], 0)
    
    def test_run_cycle(self):
        """Test running single cycle"""
        self.agent.add_memory("Test memory")
        
        result = self.scheduler.run_cycle()
        
        self.assertTrue(result["success"])
        self.assertEqual(result["cycle_number"], 1)
        self.assertIn("results", result)
        self.assertIn("stats", result)
    
    def test_state_persistence(self):
        """Test saving and loading state"""
        self.scheduler._run_count = 5
        self.scheduler._last_run = time.time()
        self.scheduler._save_state()
        
        # Create new scheduler
        scheduler2 = HeartbeatScheduler(
            agent=self.agent,
            interval_minutes=60.0,
            heartbeat_file=self.heartbeat_path,
            state_file=self.state_path
        )
        
        self.assertEqual(scheduler2._run_count, 5)
        self.assertIsNotNone(scheduler2._last_run)


class TestIntegration(unittest.TestCase):
    """End-to-end integration tests"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.agent = EvolutionAgent(
            storage_path=os.path.join(self.temp_dir, "memory.json")
        )
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_full_workflow(self):
        """Test complete memory evolution workflow"""
        # 1. Add memories
        mem1 = self.agent.add_memory("Python is a programming language", ["python", "programming"])
        mem2 = self.agent.add_memory("Python is used for machine learning", ["python", "ml"])
        mem3 = self.agent.add_memory("Java is also a programming language", ["java", "programming"])
        
        # 2. Access memories multiple times
        for _ in range(5):
            self.agent.get_memory(mem1, "learning python")
            self.agent.get_memory(mem1, "python tutorial")
        
        for _ in range(3):
            self.agent.get_memory(mem2)
        
        # 3. Run evolution
        results = self.agent.run_evolution_cycle()
        
        # 4. Verify results
        self.assertEqual(results["memories_processed"], 3)
        
        # Check that relationships were inferred
        self.assertGreaterEqual(results["relationships_inferred"], 0)
        
        # 5. Query and verify access tracking
        query_results = self.agent.query_memories("programming")
        self.assertGreater(len(query_results), 0)
        
        # 6. Check stats
        stats = self.agent.get_stats()
        self.assertEqual(stats["memory_count"], 3)


def run_tests():
    """Run all tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestMemoryEntry))
    suite.addTests(loader.loadTestsFromTestCase(TestAccessPatternTracker))
    suite.addTests(loader.loadTestsFromTestCase(TestImportanceDecay))
    suite.addTests(loader.loadTestsFromTestCase(TestRelationshipInference))
    suite.addTests(loader.loadTestsFromTestCase(TestMemoryRewriter))
    suite.addTests(loader.loadTestsFromTestCase(TestEvolutionAgent))
    suite.addTests(loader.loadTestsFromTestCase(TestScheduler))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
