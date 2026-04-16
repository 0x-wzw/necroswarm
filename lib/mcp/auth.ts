export function resolveAuthToken(authRef?: string): string | undefined {
  if (!authRef) {
    return undefined;
  }

  const token = process.env[authRef];
  if (!token) {
    return undefined;
  }

  return token;
}
