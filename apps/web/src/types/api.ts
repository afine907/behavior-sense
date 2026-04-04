export interface ApiResponse<T = unknown> {
  code: number;
  message: string;
  data: T;
  traceId?: string;
}

export interface PaginatedResponse<T> {
  total: number;
  page: number;
  size: number;
  list: T[];
}

export interface ApiError {
  code: number;
  message: string;
}
