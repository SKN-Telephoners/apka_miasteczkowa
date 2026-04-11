import React, { useMemo } from 'react';
import { View, Image, StyleSheet, StyleProp, ViewStyle } from 'react-native';
import { useTheme } from '../contexts/ThemeContext';
import { THEME } from '../utils/constants';

interface AvatarProps {
    uri?: string;
    size?: number;
    style?: StyleProp<ViewStyle>;
}

const Avatar = ({ uri, size = 80, style }: AvatarProps) => {
    const { colors } = useTheme();
    const styles = useMemo(() => getStyles(colors), [colors]);

    return (
        <View style={[styles.container, { width: size, height: size }, style]}>
            {uri ? (
                <Image source={{ uri }} style={styles.image} />
            ) : (
                <View style={styles.placeholder} />
            )}
        </View>
    );
};

const getStyles = (colors: typeof THEME.colors.light) => StyleSheet.create({
    container: {
        borderRadius: THEME.borderRadius.round,
        overflow: 'hidden',
        borderWidth: 2,
        borderColor: colors.text,
        backgroundColor: colors.border,
    },
    image: {
        width: "100%",
        height: "100%",
        resizeMode: "cover",
    },
    placeholder: {
        flex: 1,
        backgroundColor: colors.border,
    }
});

export default Avatar;
