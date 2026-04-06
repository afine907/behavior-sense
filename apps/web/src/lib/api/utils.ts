/**
 * Convert an object with various value types to a Record<string, string>
 * suitable for use as search params in API requests.
 * Filters out undefined and null values.
 */
export function toSearchParams<T extends object>(
  params: T
): Record<string, string> {
  const result: Record<string, string> = {};
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      result[key] = String(value);
    }
  });
  return result;
}
