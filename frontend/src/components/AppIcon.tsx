import React from 'react';
import { View, StyleProp, ViewStyle } from 'react-native';

import Iconset1 from '../../assets/iconset1.svg';
import Iconset2 from '../../assets/iconset2.svg';

export const ICON_REGISTRY = {
  // --- ICONSET 1 ---
  Search: { Component: Iconset1, cols: 3, rows: 3, col: 0, row: 0 },
  Sliders: { Component: Iconset1, cols: 3, rows: 3, col: 1, row: 0 },
  Home: { Component: Iconset1, cols: 3, rows: 3, col: 2, row: 0 },
  Map: { Component: Iconset1, cols: 3, rows: 3, col: 0, row: 1 },
  Events: { Component: Iconset1, cols: 3, rows: 3, col: 1, row: 1 },
  Eye: { Component: Iconset1, cols: 3, rows: 3, col: 2, row: 1 },
  Heart: { Component: Iconset1, cols: 3, rows: 3, col: 0, row: 2 },
  Comment: { Component: Iconset1, cols: 3, rows: 3, col: 1, row: 2 },
  Share: { Component: Iconset1, cols: 3, rows: 3, col: 2, row: 2 },
  AddUser: { Component: Iconset1, cols: 3, rows: 3, col: 2, row: 1 },

  // --- ICONSET 2 ---
  MoreVertical: { Component: Iconset2, cols: 3, rows: 3, col: 0, row: 0 },
  Settings: { Component: Iconset2, cols: 3, rows: 3, col: 1, row: 0 },
  Plus: { Component: Iconset2, cols: 3, rows: 3, col: 2, row: 0 },
  ArrowLeft: { Component: Iconset2, cols: 3, rows: 3, col: 0, row: 1 },
  ArrowDown: { Component: Iconset2, cols: 3, rows: 3, col: 1, row: 1 },
  Edit: { Component: Iconset2, cols: 3, rows: 3, col: 2, row: 1 },
  Preview: { Component: Iconset2, cols: 3, rows: 3, col: 0, row: 2 },
  Camera: { Component: Iconset2, cols: 3, rows: 3, col: 1, row: 2 },
  Bell: { Component: Iconset2, cols: 3, rows: 3, col: 2, row: 2 },
  Trash: { Component: Iconset2, cols: 3, rows: 3, col: 1, row: 0 },
  Send: { Component: Iconset2, cols: 3, rows: 3, col: 2, row: 0 },
} as const;

export type IconName = keyof typeof ICON_REGISTRY;

interface BaseSpriteCropperProps {
  Component: React.FC<any>;
  cols: number;
  rows: number;
  colIndex: number;
  rowIndex: number;
  size: number;
  focused?: boolean;
  style?: StyleProp<ViewStyle>;
}

const BaseSpriteCropper: React.FC<BaseSpriteCropperProps> = ({
  Component, cols, rows, colIndex, rowIndex, size, focused = true, style
}) => {
  // SVG iconsety zawsze mają viewport bazy 788x788, z której liczymy proporcje maskowania.
  const nativeWidth = 788;
  const nativeHeight = 788;
  const colWidth = nativeWidth / cols;
  const rowHeight = nativeHeight / rows;

  return (
    <View style={[
      {
        width: size,
        height: size,
        opacity: focused ? 1 : 0.75
      },
      style
    ]}>
      <Component 
        width="100%" 
        height="100%" 
        viewBox={`${colIndex * colWidth} ${rowIndex * rowHeight} ${colWidth} ${rowHeight}`} 
      />
    </View>
  );
};

interface AppIconProps {
  name: IconName | string;
  size?: number;
  focused?: boolean;
  style?: StyleProp<ViewStyle>;
}

const AppIcon: React.FC<AppIconProps> = ({ name, size = 30, focused = true, style }) => {
  const config = ICON_REGISTRY[name as IconName];

  if (!config) {
    console.warn(`Ikona o nazwie "${name}" nie została znaleziona w ICON_REGISTRY. Upewnij się, że ją zdefiniowałeś.`);
    return <View style={[{ width: size, height: size, backgroundColor: '#888' }, style]} />;
  }

  return (
    <BaseSpriteCropper
      Component={config.Component}
      cols={config.cols}
      rows={config.rows}
      colIndex={config.col}
      rowIndex={config.row}
      size={size}
      focused={focused}
      style={style}
    />
  );
};

export default AppIcon;
