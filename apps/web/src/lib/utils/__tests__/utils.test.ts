import { cn } from '../cn';
import { formatNumber, formatPercent, formatCurrency } from '../format';

describe('cn (className utility)', () => {
  it('should merge class names', () => {
    expect(cn('foo', 'bar')).toBe('foo bar');
  });

  it('should handle conditional classes', () => {
    expect(cn('foo', false && 'bar', 'baz')).toBe('foo baz');
  });

  it('should merge tailwind classes correctly', () => {
    // tailwind-merge should dedupe conflicting classes
    expect(cn('px-2', 'px-4')).toBe('px-4');
    expect(cn('text-red-500', 'text-blue-500')).toBe('text-blue-500');
  });

  it('should handle undefined and null', () => {
    expect(cn('foo', undefined, null, 'bar')).toBe('foo bar');
  });

  it('should handle arrays', () => {
    expect(cn(['foo', 'bar'], 'baz')).toBe('foo bar baz');
  });

  it('should handle objects', () => {
    expect(cn({ foo: true, bar: false, baz: true })).toBe('foo baz');
  });
});

describe('formatNumber', () => {
  it('should format numbers with Chinese locale', () => {
    expect(formatNumber(1000)).toBe('1,000');
    expect(formatNumber(1234567)).toBe('1,234,567');
  });

  it('should handle decimal numbers', () => {
    expect(formatNumber(1234.56)).toBe('1,234.56');
  });

  it('should handle zero', () => {
    expect(formatNumber(0)).toBe('0');
  });

  it('should handle negative numbers', () => {
    expect(formatNumber(-1000)).toBe('-1,000');
  });
});

describe('formatPercent', () => {
  it('should format percentages correctly', () => {
    expect(formatPercent(0.5)).toBe('50%');
    expect(formatPercent(0.123)).toBe('12.3%');
  });

  it('should respect maximumFractionDigits', () => {
    expect(formatPercent(0.12345)).toBe('12.35%');
  });

  it('should handle zero', () => {
    expect(formatPercent(0)).toBe('0%');
  });

  it('should handle values greater than 1', () => {
    expect(formatPercent(1.5)).toBe('150%');
  });
});

describe('formatCurrency', () => {
  it('should format currency with CNY by default', () => {
    expect(formatCurrency(1000)).toMatch(/¥/);
    expect(formatCurrency(1000)).toContain('1,000');
  });

  it('should support different currencies', () => {
    expect(formatCurrency(1000, 'USD')).toContain('$');
    expect(formatCurrency(1000, 'EUR')).toContain('€');
  });

  it('should handle decimal values', () => {
    const result = formatCurrency(1234.56);
    expect(result).toContain('1,234');
  });
});
