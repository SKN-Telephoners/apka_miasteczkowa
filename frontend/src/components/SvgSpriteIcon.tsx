import React from "react";
import { StyleProp, ViewStyle } from "react-native";

import Iconset1 from "../../assets/iconset1.svg";
import Iconset2 from "../../assets/iconset2.svg";

const BASE_TILE_SIZE = 30;
const GRID_SIZE = 3;
const NATIVE_SVG_SIZE = 788;
const TILE_VIEWBOX_SIZE = NATIVE_SVG_SIZE / GRID_SIZE;

const clampIndex = (value: number) => {
  if (value < 0) return 0;
  if (value > GRID_SIZE - 1) return GRID_SIZE - 1;
  return value;
};

interface SvgSpriteIconProps {
  set: 1 | 2;
  size: number;
  offsetX?: number;
  offsetY?: number;
  style?: StyleProp<ViewStyle>;
}

const SvgSpriteIcon: React.FC<SvgSpriteIconProps> = ({
  set,
  size,
  offsetX = 0,
  offsetY = 0,
  style,
}) => {
  const col = clampIndex(Math.round(-offsetX / BASE_TILE_SIZE));
  const row = clampIndex(Math.round(-offsetY / BASE_TILE_SIZE));

  const Component = set === 1 ? Iconset1 : Iconset2;

  return (
    <Component
      width={size}
      height={size}
      style={style}
      viewBox={`${col * TILE_VIEWBOX_SIZE} ${row * TILE_VIEWBOX_SIZE} ${TILE_VIEWBOX_SIZE} ${TILE_VIEWBOX_SIZE}`}
    />
  );
};

export default SvgSpriteIcon;
