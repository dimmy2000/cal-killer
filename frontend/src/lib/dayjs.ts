import dayjs from "dayjs";
import utc from "dayjs/plugin/utc";
import timezone from "dayjs/plugin/timezone";
import "dayjs/locale/ru";
import customParseFormat from "dayjs/plugin/customParseFormat";
import isToday from "dayjs/plugin/isToday";
import isTomorrow from "dayjs/plugin/isTomorrow";

dayjs.extend(utc);
dayjs.extend(timezone);
dayjs.extend(customParseFormat);
dayjs.extend(isToday);
dayjs.extend(isTomorrow);
dayjs.locale("ru");

export { dayjs };

export function formatTime(utcIso: string, tz: string): string {
  return dayjs.utc(utcIso).tz(tz).format("HH:mm");
}

export function formatDateTime(utcIso: string, tz: string): string {
  return dayjs.utc(utcIso).tz(tz).format("D MMMM YYYY, HH:mm");
}

export function formatDate(utcIso: string, tz: string): string {
  return dayjs.utc(utcIso).tz(tz).format("D MMMM YYYY");
}

export function formatDateShort(date: string | Date): string {
  return dayjs(date).format("YYYY-MM-DD");
}

export function formatDuration(minutes: number): string {
  if (minutes < 60) return `${minutes} мин`;
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return m === 0 ? `${h} ч` : `${h} ч ${m} мин`;
}

export function minutesToTime(minutes: number): string {
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}`;
}

export function timeToMinutes(time: string): number {
  const [h, m] = time.split(":").map(Number);
  return h * 60 + m;
}

export function getLocalTimezone(): string {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC";
  } catch {
    return "UTC";
  }
}
