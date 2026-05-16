export type ApiSuccess<T> = {
  code: number | string;
  message: string;
  data: T;
};

export type FieldErrorMap = Record<string, string[] | string>;

export class ApiError extends Error {
  status: number;
  code?: number | string;
  fieldErrors?: FieldErrorMap;

  constructor(message: string, status: number, code?: number | string, fieldErrors?: FieldErrorMap) {
    super(message);
    this.status = status;
    this.code = code;
    this.fieldErrors = fieldErrors;
  }
}
