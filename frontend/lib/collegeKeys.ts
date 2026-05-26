import type { CollegeOption } from "./api";

/** Stable id for compare / selection (program is unique per row). */
export function rowId(c: CollegeOption): string {
  if (c.program_id != null) return `p-${c.program_id}`;
  return `${c.college_name}|${c.program_name}|${c.closing_rank}|${c.quota}`;
}

/** React list key — guaranteed unique without depending on index position.
 * This prevents duplicate key errors even with duplicate program_ids.
 */
export function listKey(c: CollegeOption, index: number): string {
  // Create unique key from college identifier + index to ensure uniqueness
  const baseKey = c.program_id != null 
    ? `prog-${c.program_id}`
    : `college-${c.college_name}|${c.program_name}|${c.closing_rank}|${c.quota}`;
  return `${baseKey}:${index}`;
}
