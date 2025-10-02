declare module "react" {
  export type Dispatch<A> = (value: A | ((prev: A) => A)) => void;

  export interface BaseSyntheticEvent<T = unknown> {
    target: T;
    preventDefault(): void;
  }

  export interface ChangeEvent<T = { value: string }> extends BaseSyntheticEvent<T> {}

  export interface FormEvent<T = unknown> extends BaseSyntheticEvent<T> {}

  export function useState<S>(initialState: S | (() => S)): [S, Dispatch<S>];
}

declare module "react/jsx-runtime" {
  export const jsx: unknown;
  export const jsxs: unknown;
  export const Fragment: unknown;
}

declare namespace JSX {
  interface Element {}
  interface IntrinsicElements {
    [elemName: string]: Record<string, unknown>;
  }
}
