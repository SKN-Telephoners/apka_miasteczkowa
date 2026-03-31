import React from 'react';
import { View, Image, ImageSourcePropType, StyleProp, ViewStyle } from 'react-native';

export const ICON_REGISTRY = {
  // Prawy górny róg w iconset1.jpg (kolumna 2, wiersz 0)
  'Home': { source: require('../../assets/iconset1.jpg'), sheetWidth: 90, sheetHeight: 90, iconWidth: 30, iconHeight: 30, col: 2, row: 0 },

  // Lewa strona środek (kolumna 0, wiersz 1)
  'Mapa': { source: require('../../assets/iconset1.jpg'), sheetWidth: 90, sheetHeight: 90, iconWidth: 30, iconHeight: 30, col: 0, row: 1 },

  // Samo centrum (kolumna 1, wiersz 1)
  'Wydarzenia': { source: require('../../assets/iconset1.jpg'), sheetWidth: 90, sheetHeight: 90, iconWidth: 30, iconHeight: 30, col: 1, row: 1 },

  // Prawa strona środek (kolumna 2, wiersz 1)
  'Profil': { source: require('../../assets/iconset1.jpg'), sheetWidth: 90, sheetHeight: 90, iconWidth: 30, iconHeight: 30, col: 2, row: 1 },

} as const;

export type IconName = keyof typeof ICON_REGISTRY;

interface BaseSpriteCropperProps {
  source: ImageSourcePropType;
  sheetWidth: number;
  sheetHeight: number;
  iconWidth: number;
  iconHeight: number;
  colIndex: number;
  rowIndex: number;
  size: number;
  focused?: boolean;
  style?: StyleProp<ViewStyle>;
}

const BaseSpriteCropper: React.FC<BaseSpriteCropperProps> = ({
  source, sheetWidth, sheetHeight, iconWidth, iconHeight, colIndex, rowIndex, size, focused = true, style
}) => {
  // Obliczamy skalowanie, żeby np. oryginalna 30x30 zmieściła się w rozmiarze size=50 
  const scale = size / iconWidth;
  const offsetX = -(colIndex * iconWidth) * scale;
  const offsetY = -(rowIndex * iconHeight) * scale;

  return (
    <View style={[
      {
        width: size,
        height: size,
        overflow: 'hidden',
        opacity: focused ? 1 : 0.4
      },
      style
    ]}>
      <Image
        source={source}
        style={{
          width: sheetWidth * scale,
          height: sheetHeight * scale,
          // Przesunięcie "pod" ramką aby odsłonić tylko żądaną komórkę siatki
          transform: [
            { translateX: offsetX },
            { translateY: offsetY }
          ]
        }}
        resizeMode="cover"
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
  const config = ICON_REGISTRY[name];

  if (!config) {
    console.warn(`Ikona o nazwie "${name}" nie została znaleziona w ICON_REGISTRY. Upewnij się, że ją zdefiniowałeś.`);
    return <View style={[{ width: size, height: size, backgroundColor: '#888' }, style]} />;
  }

  return (
    <BaseSpriteCropper
      source={config.source}
      sheetWidth={config.sheetWidth}
      sheetHeight={config.sheetHeight}
      iconWidth={config.iconWidth}
      iconHeight={config.iconHeight}
      colIndex={config.col}
      rowIndex={config.row}
      size={size}
      focused={focused}
      style={style}
    />
  );
};

export default AppIcon;
