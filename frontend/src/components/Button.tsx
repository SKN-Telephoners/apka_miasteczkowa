import React from 'react';
import {
    TouchableOpacity,
    Text,
    StyleSheet,
    TouchableOpacityProps,
    ActivityIndicator,
    ViewStyle,
    TextStyle
} from 'react-native';
import { THEME } from '../../utils/constants';

interface ButtonProps extends TouchableOpacityProps {
    title: string;
    loading?: boolean;
    type?: 'primary' | 'secondary' | 'outline';
    style?: ViewStyle;
    textStyle?: TextStyle;
}

const Button: React.FC<ButtonProps> = ({
    title,
    onPress,
    loading = false,
    type = 'primary',
    disabled,
    style,
    textStyle,
    ...rest
}) => {

    const getButtonStyle = () => {
        switch (type) {
            case 'secondary':
                return styles.secondaryButton;
            case 'outline':
                return styles.outlineButton;
            case 'primary':
            default:
                return styles.primaryButton;
        }
    };

    const getTextStyle = () => {
        switch (type) {
            case 'secondary':
                return styles.secondaryText;
            case 'outline':
                return styles.outlineText;
            case 'primary':
            default:
                return styles.primaryText;
        }
    };

    return (
        <TouchableOpacity
            style={[
                styles.button,
                getButtonStyle(),
                disabled ? styles.disabledButton : null,
                style
            ]}
            onPress={onPress}
            disabled={disabled || loading}
            activeOpacity={0.8}
            {...rest}
        >
            {loading ? (
                <ActivityIndicator color={type === 'outline' ? THEME.colors.lm_highlight : '#FFF'} />
            ) : (
                <Text style={[styles.text, getTextStyle(), textStyle]}>
                    {title}
                </Text>
            )}
        </TouchableOpacity>
    );
};

const styles = StyleSheet.create({
    button: {
        width: '100%',
        height: 48,
        borderRadius: THEME.borderRadius.m,
        justifyContent: 'center',
        alignItems: 'center',
        flexDirection: 'row',
        marginVertical: THEME.spacing.s,
    },
    primaryButton: {
        backgroundColor: THEME.colors.lm_highlight,
    },
    secondaryButton: {
        backgroundColor: THEME.colors.lm_src_br,
    },
    outlineButton: {
        backgroundColor: 'transparent',
        borderWidth: 1,
        borderColor: THEME.colors.lm_highlight,
    },
    disabledButton: {
        opacity: 0.5,
    },
    text: {
        ...THEME.typography.text,
        fontWeight: 'bold',
        fontSize: 16,
    },
    primaryText: {
        color: '#FFFFFF',
    },
    secondaryText: {
        color: THEME.colors.lm_txt,
    },
    outlineText: {
        color: THEME.colors.lm_highlight,
    }
});

export default Button;
