export type LocationCoordinates = [number, number];

export const DEFAULT_LOCATION_COORDINATES: LocationCoordinates = [19.9061, 50.0686];

const toFiniteCoordinate = (value: unknown): number | null => {
  if (typeof value === "boolean" || value === null || value === undefined) {
    return null;
  }

  const parsed = typeof value === "number" ? value : Number(value);
  return Number.isFinite(parsed) ? Number(parsed.toFixed(6)) : null;
};

export const normalizeLocationCoordinates = (value: unknown): LocationCoordinates | null => {
  if (Array.isArray(value) && value.length >= 2) {
    const x = toFiniteCoordinate(value[0]);
    const y = toFiniteCoordinate(value[1]);

    if (x === null || y === null) {
      return null;
    }

    return [x, y];
  }

  if (typeof value === "string") {
    const trimmedValue = value.trim();
    if (!trimmedValue) {
      return null;
    }

    try {
      const parsed = JSON.parse(trimmedValue);
      const normalized = normalizeLocationCoordinates(parsed);
      if (normalized) {
        return normalized;
      }
    } catch {
      // Fall back to the compact coordinate format below.
    }

    const match = trimmedValue.match(/^\[?\s*([-+]?\d*\.?\d+)\s*,\s*([-+]?\d*\.?\d+)\s*\]?$/);
    if (!match) {
      return null;
    }

    const x = toFiniteCoordinate(match[1]);
    const y = toFiniteCoordinate(match[2]);
    return x === null || y === null ? null : [x, y];
  }

  return null;
};

export const formatLocationCoordinates = (coordinates: LocationCoordinates | null | undefined): string => {
  if (!coordinates) {
    return "Wybierz lokalizację na mapie";
  }

  return `${coordinates[0].toFixed(6)}, ${coordinates[1].toFixed(6)}`;
};

export const serializeLocationCoordinates = (coordinates: LocationCoordinates): string => {
  return `${coordinates[0].toFixed(6)},${coordinates[1].toFixed(6)}`;
};