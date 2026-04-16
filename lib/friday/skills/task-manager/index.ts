/**
 * Task Manager Skill — Issue/task tracking for agent work.
 *
 * Inspired by Paperclip's issue management system:
 * - Tasks form a hierarchy (parent/child)
 * - Single assignee with atomic checkout
 * - Status workflow: backlog → todo → in_progress → in_review → done
 * - Comment trail for audit
 */

import { defineSkill } from "../../core/define-skill.js";
import { randomUUID } from "node:crypto";

export type TaskStatus = "backlog" | "todo" | "in_progress" | "in_review" | "blocked" | "done" | "cancelled";

export interface Task {
  id: string;
  title: string;
  description?: string;
  status: TaskStatus;
  assignee?: string;
  parentId?: string;
  tags?: string[];
  createdAt: string;
  updatedAt: string;
  comments: Array<{ author: string; text: string; timestamp: string }>;
}

// In-memory task store
const tasks = new Map<string, Task>();

export const taskManagerSkill = defineSkill({
  manifest: {
    id: "task.manager",
    name: "Task Manager",
    description: "Create, assign, and track tasks with status workflows and audit trails",
    version: "0.1.0",
    tags: ["tasks", "issues", "workflow", "tracking"],
  },

  actions: [
    {
      name: "create",
      description: "Create a new task",
      inputSchema: {
        type: "object",
        properties: {
          title: { type: "string" },
          description: { type: "string" },
          parentId: { type: "string" },
          tags: { type: "array", items: { type: "string" } },
        },
        required: ["title"],
      },
      async execute(input, ctx) {
        const { title, description, parentId, tags } = input as {
          title: string;
          description?: string;
          parentId?: string;
          tags?: string[];
        };

        const task: Task = {
          id: `task_${randomUUID().slice(0, 8)}`,
          title,
          description,
          status: "backlog",
          parentId,
          tags,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
          comments: [],
        };

        tasks.set(task.id, task);
        ctx.logger.info("Task created", { taskId: task.id, title });
        ctx.emit("task.created", { task });

        return { success: true, data: task };
      },
    },

    {
      name: "checkout",
      description: "Assign a task to yourself and set it to in_progress (atomic)",
      inputSchema: {
        type: "object",
        properties: {
          taskId: { type: "string" },
        },
        required: ["taskId"],
      },
      async execute(input, ctx) {
        const { taskId } = input as { taskId: string };
        const task = tasks.get(taskId);

        if (!task) {
          return { success: false, error: `Task ${taskId} not found` };
        }

        // Atomic checkout — only one assignee (Paperclip's key invariant)
        if (task.status === "in_progress" && task.assignee && task.assignee !== ctx.agentId) {
          return {
            success: false,
            error: `Task ${taskId} is already checked out by ${task.assignee}`,
          };
        }

        task.assignee = ctx.agentId;
        task.status = "in_progress";
        task.updatedAt = new Date().toISOString();

        ctx.logger.info("Task checked out", { taskId, assignee: ctx.agentId });
        ctx.emit("task.checked_out", { taskId, assignee: ctx.agentId });

        return { success: true, data: task };
      },
    },

    {
      name: "update_status",
      description: "Update a task's status",
      inputSchema: {
        type: "object",
        properties: {
          taskId: { type: "string" },
          status: { type: "string", enum: ["backlog", "todo", "in_progress", "in_review", "blocked", "done", "cancelled"] },
        },
        required: ["taskId", "status"],
      },
      async execute(input, ctx) {
        const { taskId, status } = input as { taskId: string; status: TaskStatus };
        const task = tasks.get(taskId);

        if (!task) {
          return { success: false, error: `Task ${taskId} not found` };
        }

        const prevStatus = task.status;
        task.status = status;
        task.updatedAt = new Date().toISOString();

        ctx.logger.info("Task status updated", { taskId, from: prevStatus, to: status });
        ctx.emit("task.status_changed", { taskId, from: prevStatus, to: status });

        return { success: true, data: task };
      },
    },

    {
      name: "comment",
      description: "Add a comment to a task",
      inputSchema: {
        type: "object",
        properties: {
          taskId: { type: "string" },
          text: { type: "string" },
        },
        required: ["taskId", "text"],
      },
      async execute(input, ctx) {
        const { taskId, text } = input as { taskId: string; text: string };
        const task = tasks.get(taskId);

        if (!task) {
          return { success: false, error: `Task ${taskId} not found` };
        }

        const comment = {
          author: ctx.agentId,
          text,
          timestamp: new Date().toISOString(),
        };

        task.comments.push(comment);
        task.updatedAt = new Date().toISOString();

        ctx.logger.info("Comment added", { taskId, author: ctx.agentId });
        ctx.emit("task.commented", { taskId, comment });

        return { success: true, data: { task, comment } };
      },
    },

    {
      name: "list",
      description: "List tasks, optionally filtered by status or assignee",
      inputSchema: {
        type: "object",
        properties: {
          status: { type: "string" },
          assignee: { type: "string" },
          parentId: { type: "string" },
        },
      },
      async execute(input, _ctx) {
        const { status, assignee, parentId } = (input as {
          status?: string;
          assignee?: string;
          parentId?: string;
        }) ?? {};

        let results = Array.from(tasks.values());

        if (status) results = results.filter((t) => t.status === status);
        if (assignee) results = results.filter((t) => t.assignee === assignee);
        if (parentId) results = results.filter((t) => t.parentId === parentId);

        return { success: true, data: { tasks: results, count: results.length } };
      },
    },

    {
      name: "get",
      description: "Get a single task by ID",
      inputSchema: {
        type: "object",
        properties: {
          taskId: { type: "string" },
        },
        required: ["taskId"],
      },
      async execute(input, _ctx) {
        const { taskId } = input as { taskId: string };
        const task = tasks.get(taskId);

        if (!task) {
          return { success: false, error: `Task ${taskId} not found` };
        }

        return { success: true, data: task };
      },
    },
  ],

  async setup(ctx) {
    ctx.logger.info("Task manager skill loaded");
  },
});

export default taskManagerSkill;
