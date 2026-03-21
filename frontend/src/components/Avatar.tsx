import React from 'react';
import { View, Image, StyleSheet, StyleProp, ViewStyle } from 'react-native';
import { THEME } from '../utils/constants';

interface AvatarProps {
    uri?: string;
    size?: number;
    style?: StyleProp<ViewStyle>;
}

const Avatar = ({ uri, size = 80, style }: AvatarProps) => {
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

const styles = StyleSheet.create({
    container: {
        borderRadius: THEME.borderRadius.round,
        overflow: 'hidden',
        borderWidth: 2,
        borderColor: THEME.colors.lm_src_br,
        backgroundColor: THEME.colors.lm_src_br,
    },
    image: {
        width: "100%",
        height: "100%",
        resizeMode: "cover",
    },
    placeholder: {
        flex: 1,
        backgroundColor: THEME.colors.lm_src_br,
    }
});

export default Avatar;
