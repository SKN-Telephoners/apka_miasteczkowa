import React from "react";
import {
  ActivityIndicator,
  StyleProp,
  StyleSheet,
  Text,
  TextStyle,
  TouchableOpacity,
  TouchableOpacityProps,
  ViewStyle,
} from "react-native";
import { useTheme } from "../contexts/ThemeContext";
import { THEME } from "../utils/constants";

interface ButtonProps extends TouchableOpacityProps {
  title: string;
  loading?: boolean;
  type?: "primary" | "secondary" | "outline";
  style?: StyleProp<ViewStyle>;
  textStyle?: StyleProp<TextStyle>;
}

const Button: React.FC<ButtonProps> = ({
  title,
  onPress,
  loading = false,
  type = "primary",
  disabled,
  style,
  textStyle,
  ...rest
}) => {
  const { colors } = useTheme();
  const styles = React.useMemo(() => getStyles(colors), [colors]);

  const getButtonStyle = () => {
    switch (type) {
      case "secondary":
        return styles.secondaryButton;
      case "outline":
        return styles.outlineButton;
      case "primary":
      default:
        return styles.primaryButton;
    }
  };

  const getTextStyle = () => {
    switch (type) {
      case "secondary":
        return styles.secondaryText;
      case "outline":
        return styles.outlineText;
      case "primary":
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
        style,
      ]}
      onPress={onPress}
      disabled={disabled || loading}
      activeOpacity={0.8}
      {...rest}
    >
      {loading ? (
        <ActivityIndicator
          color={
            type === "outline"
              ? THEME.colors.light.transparentHighlight
              : "#FFF"
          }
        />
      ) : (
        <Text style={[styles.text, getTextStyle(), textStyle]}>{title}</Text>
      )}
    </TouchableOpacity>
  );
};

const getStyles = (colors: typeof THEME.colors.light) =>
  StyleSheet.create({
    button: {
      width: "100%",
      height: 48,
      borderRadius: THEME.borderRadius.m,
      justifyContent: "center",
      alignItems: "center",
      flexDirection: "row",
      marginVertical: THEME.spacing.s,
    },
    primaryButton: {
      backgroundColor: colors.highlight,
    },
    secondaryButton: {
      backgroundColor: colors.border,
    },
    outlineButton: {
      backgroundColor: colors.background,
      borderWidth: 1,
      borderColor: colors.highlight,
    },
    disabledButton: {
      opacity: 0.5,
    },
    text: {
      ...THEME.typography.text,
      fontWeight: "700",
    },
    primaryText: {
      color: "#FFFFFF",
    },
    secondaryText: {
      color: colors.text,
      textDecorationLine: "underline",
    },
    outlineText: {
      color: colors.highlight,
      textDecorationLine: "underline",
    },
  });

export default Button;
