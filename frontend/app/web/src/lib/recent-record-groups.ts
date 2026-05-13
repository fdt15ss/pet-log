import type { RecordCategory, RecordEntry } from "./types";

export type RecentRecordCardGroup = {
  id: string;
  date: string;
  time: string;
  categories: RecordCategory[];
  records: RecordEntry[];
};

export function groupRecentRecordCards(records: RecordEntry[], maxGroups = 3): RecentRecordCardGroup[] {
  const groups: RecentRecordCardGroup[] = [];

  for (const record of records) {
    const previousGroup = groups[groups.length - 1];
    if (previousGroup && previousGroup.date === record.date && previousGroup.time === record.time) {
      previousGroup.records.push(record);
      if (!previousGroup.categories.includes(record.category)) {
        previousGroup.categories.push(record.category);
      }
      continue;
    }

    if (groups.length >= maxGroups) {
      break;
    }

    groups.push({
      id: record.id,
      date: record.date,
      time: record.time,
      categories: [record.category],
      records: [record],
    });
  }

  return groups;
}
