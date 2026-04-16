import Ajv2020, { ErrorObject, ValidateFunction } from "ajv/dist/2020";
import addFormats from "ajv-formats";

import taskSpecSchema from "@/lib/schemas/task_spec.schema.json";
import preflightReportSchema from "@/lib/schemas/preflight_report.schema.json";
import botPackageSchema from "@/lib/schemas/bot_package.schema.json";
import auditReportSchema from "@/lib/schemas/audit_report.schema.json";
import deploySpecSchema from "@/lib/schemas/deploy_spec.schema.json";
import deployResultSchema from "@/lib/schemas/deploy_result.schema.json";

const ajv = new Ajv2020({ allErrors: true, strict: true });
addFormats(ajv);

type SchemaName = "taskSpec" | "preflight" | "botPackage" | "auditReport" | "deploySpec" | "deployResult";

const validators: Record<SchemaName, ValidateFunction> = {
  taskSpec: ajv.compile(taskSpecSchema),
  preflight: ajv.compile(preflightReportSchema),
  botPackage: ajv.compile(botPackageSchema),
  auditReport: ajv.compile(auditReportSchema),
  deploySpec: ajv.compile(deploySpecSchema),
  deployResult: ajv.compile(deployResultSchema)
};

const formatError = (errors: ErrorObject[] | null | undefined): string => {
  if (!errors?.length) {
    return "Schema validation failed with unknown error.";
  }

  return errors
    .map((error) => `${error.instancePath || "/"} ${error.message ?? "is invalid"}`)
    .join("; ");
};

export function assertValidSchema<T>(name: SchemaName, payload: unknown): asserts payload is T {
  const validator = validators[name];
  const valid = validator(payload);

  if (!valid) {
    throw new Error(`Invalid ${name}: ${formatError(validator.errors)}`);
  }
}
