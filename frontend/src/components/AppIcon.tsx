import React from 'react';
import { View, Image, ImageSourcePropType, StyleProp, ViewStyle } from 'react-native';

//=============================================================================
// 1. REJESTR IKON (Uzupełniaj go w miarę dodawania nowych ikon do projektu)
//=============================================================================

export const ICON_REGISTRY = {
  // Prawy górny róg w iconset1.jpg (kolumna 2, wiersz 0)
  'Home': { source: require('../../assets/iconset1.jpg'), sheetWidth: 90, sheetHeight: 90, iconWidth: 30, iconHeight: 30, col: 2, row: 0 },

  // Lewa strona środek (kolumna 0, wiersz 1)
  'Mapa': { source: require('../../assets/iconset1.jpg'), sheetWidth: 90, sheetHeight: 90, iconWidth: 30, iconHeight: 30, col: 0, row: 1 },

  // Samo centrum (kolumna 1, wiersz 1)
  'Wydarzenia': { source: require('../../assets/iconset1.jpg'), sheetWidth: 90, sheetHeight: 90, iconWidth: 30, iconHeight: 30, col: 1, row: 1 },

  // Prawa strona środek (kolumna 2, wiersz 1)
  'Profil': { source: require('../../assets/iconset1.jpg'), sheetWidth: 90, sheetHeight: 90, iconWidth: 30, iconHeight: 30, col: 2, row: 1 },

  // Przykład jak można dodać ikonę z zupełnie innego pliku/sprite'a
  // 'InnaIkona': { source: require('../../assets/innySprite.png'), sheetWidth: 120, sheetHeight: 60, iconWidth: 60, iconHeight: 60, col: 0, row: 0 },
} as const;

export type IconName = keyof typeof ICON_REGISTRY;

//=============================================================================
// 2. LOGIKA WYCINANIA (Dzięki niej nie musisz już myśleć o offsetach XYZ)
//=============================================================================

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

//=============================================================================
// 3. KOMPONENT GŁÓWNY, z którego zawsze będziesz korzystać w projekcie.
//=============================================================================

interface AppIconProps {
  /** Nazwa ikony (np. zdefiniowanej w ICON_REGISTRY w tym pliku) */
  name: IconName | string; // Wymuszamy typowanie dla podpowiedzi IDE, ale dajemy elastyczność fallbacku
  /** Rozmiar ikony docelowo wyświetlanej na ekranie */
  size?: number;
  /** Jasność (jeśli ikona jest w pasku aktualnie aktywna - 1; jeśli nie - 0.4) */
  focused?: boolean;
  /** Zewnętrzne style (marginesy itd.) */
  style?: StyleProp<ViewStyle>;
}

const AppIcon: React.FC<AppIconProps> = ({ name, size = 30, focused = true, style }) => {
  // Wydobywamy z rejestru parametry zarejestrowanej uprzednio figury
  // @ts-ignore
  const config = ICON_REGISTRY[name];

  if (!config) {
    // Gdyby ktoś podał ikonę, której jeszcze nie wpisaliśmy do rejestru wyżej, renderujemy szary kwadrat 'fallback'
    console.warn(`Ikona o nazwie "${name}" nie została znaleziona w ICON_REGISTRY. Upewnij się, że ją zdefiniowałeś.`);
    return <View style={[{ width: size, height: size, backgroundColor: '#888' }, style]} />;
  }

  // Oddelegowujemy czarną magię wycinanej siatki w dół
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
