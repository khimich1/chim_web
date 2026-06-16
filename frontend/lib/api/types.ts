export type Role = "teacher" | "student";
export type Track = "ege" | "oge";

export interface User {
  id: string;
  email: string;
  role: Role;
  track: Track | null;
}
