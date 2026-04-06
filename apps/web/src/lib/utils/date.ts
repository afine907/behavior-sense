import { format, formatDistanceToNow, parseISO, isValid } from 'date-fns';
import { zhCN } from 'date-fns/locale';

export function formatDate(date: string | Date): string {
  const parsedDate = typeof date === 'string' ? parseISO(date) : date;
  if (!isValid(parsedDate)) {
    return '-';
  }
  return format(parsedDate, 'yyyy-MM-dd HH:mm:ss', { locale: zhCN });
}

export function formatDateShort(date: string | Date): string {
  const parsedDate = typeof date === 'string' ? parseISO(date) : date;
  if (!isValid(parsedDate)) {
    return '-';
  }
  return format(parsedDate, 'yyyy-MM-dd', { locale: zhCN });
}

export function formatRelative(date: string | Date): string {
  const parsedDate = typeof date === 'string' ? parseISO(date) : date;
  if (!isValid(parsedDate)) {
    return '-';
  }
  return formatDistanceToNow(parsedDate, { addSuffix: true, locale: zhCN });
}

export function formatTime(date: string | Date): string {
  const parsedDate = typeof date === 'string' ? parseISO(date) : date;
  if (!isValid(parsedDate)) {
    return '-';
  }
  return format(parsedDate, 'HH:mm:ss', { locale: zhCN });
}
