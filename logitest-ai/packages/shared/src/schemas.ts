import { z } from "zod";

export const HealthResponseSchema = z.object({
  status: z.literal("ok"),
});

export const ApiErrorSchema = z.object({
  message: z.string(),
  code: z.string().optional(),
});

export type HealthResponse = z.infer<typeof HealthResponseSchema>;
export type ApiError = z.infer<typeof ApiErrorSchema>;
