import { Ionicons } from "@expo/vector-icons";
import React, { useState } from "react";
import {
  TextStyle,
  TextInputProps,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import { useMemo } from "react";
import { useTheme } from "../contexts/ThemeContext";
import { THEME } from '../utils/constants';
import SvgSpriteIcon from "./SvgSpriteIcon";

interface InputFieldProps {
  placeholder: string;
  value: string;
  onChangeText: (text: string) => void;
  secureTextEntry?: boolean;
  toggleSecure?: () => void;
  errorMessage?: string;
  validate?: (text: string) => string | null;
  autoCapitalize?: "none" | "sentences" | "words" | "characters";
  showSearchSpriteIcon?: boolean;
  reserveErrorSpace?: boolean;
  autoComplete?: TextInputProps["autoComplete"];
  textContentType?: TextInputProps["textContentType"];
  importantForAutofill?: TextInputProps["importantForAutofill"];
  showFloatingLabel?: boolean;
  floatingLabelColor?: TextStyle["color"];
  floatingLabelBackgroundColor?: TextStyle["backgroundColor"];
}

const BASE_TILE_SIZE = 30;
const ICON_SIZE = 18;

const InputField: React.FC<InputFieldProps> = ({
  placeholder,
  value,
  onChangeText,
  secureTextEntry,
  toggleSecure,
  errorMessage,
  validate,
  autoCapitalize = "none",
  showSearchSpriteIcon = false,
  reserveErrorSpace = true,
  autoComplete,
  textContentType,
  importantForAutofill,
  showFloatingLabel = true,
  floatingLabelColor = THEME.colors.light.text,
  floatingLabelBackgroundColor = THEME.colors.light.background,
}) => {
  const { colors, isDark } = useTheme();
  const styles = useMemo(() => getStyles(colors), [colors]);
  const [localErrorMessage, setLocalErrorMessage] = useState<string | null>(
    null
  );
  const [isTouched, setIsTouched] = useState(false);

  const isEmpty = value === "";

  const handleTextChange = (text: string) => {
    onChangeText(text);

    // Validate while typing if already touched
    if (isTouched && validate) {
      const validationError = validate(text);
      setLocalErrorMessage(validationError);
    }
  };

  const handleBlur = () => {
    setIsTouched(true);

    if (validate) {
      const validationError = validate(value);
      setLocalErrorMessage(validationError);
    }
  };

  const handleFocus = () => {
    // Clear local validation error when focusing on the input again
    setLocalErrorMessage(null);
  };

  // Prioritize local validation over external error message
  const displayErrorMessage = isTouched
    ? localErrorMessage ?? errorMessage
    : null;

  const resolvedFloatingLabelColor = floatingLabelColor ?? colors.text;
  const resolvedFloatingLabelBackgroundColor = floatingLabelBackgroundColor ?? colors.background;
  const resolvedPlaceholderTextColor = showSearchSpriteIcon && isDark ? colors.text : colors.searchWord;

  return (
    <View style={styles.container}>
      <View
        style={[
          styles.inputBox,
          displayErrorMessage ? styles.inputBoxError : null,
        ]}
      >
        {!isEmpty && showFloatingLabel && (
          <Text
            style={[
              styles.legend,
              { color: resolvedFloatingLabelColor, backgroundColor: resolvedFloatingLabelBackgroundColor },
            ]}
          >
            {placeholder}
          </Text>
        )}
        <TextInput
          style={styles.input}
          placeholder={placeholder}
          placeholderTextColor={resolvedPlaceholderTextColor}
          value={value}
          onChangeText={handleTextChange}
          onBlur={handleBlur}
          onFocus={handleFocus}
          secureTextEntry={secureTextEntry}
          accessibilityLabel={placeholder}
          accessibilityHint={displayErrorMessage || undefined}
          autoCapitalize={autoCapitalize}
          autoComplete={autoComplete}
          textContentType={textContentType}
          importantForAutofill={importantForAutofill}
        />
        {toggleSecure && (
          <TouchableOpacity onPress={toggleSecure}>
            <Ionicons
              name={secureTextEntry ? "eye-off-outline" : "eye-outline"}
              size={20}
              color={colors.transparentHighlight}
            />
          </TouchableOpacity>
        )}
        {!toggleSecure && showSearchSpriteIcon && (
          <View style={styles.searchIconContainer}>
            <SvgSpriteIcon set={1} size={ICON_SIZE} />
          </View>
        )}
      </View>

      <Text
        style={[
          styles.errorMessage,
          !reserveErrorSpace && !displayErrorMessage ? styles.errorMessageHidden : null,
        ]}
      >
        {displayErrorMessage}
      </Text>
    </View>
  );
};

const getStyles = (colors: typeof THEME.colors.light) => StyleSheet.create({
  container: {
    marginBottom: 1,
  },
  inputBox: {
    flexDirection: "row",
    alignItems: "center",
    borderRadius: 35,
    paddingHorizontal: 10,
    height: 40,
    borderWidth: 2,
    borderColor: colors.searchWord,
    backgroundColor: colors.border,
  },
  inputBoxError: {
    borderColor: colors.aghRed,
  },
  input: {
    flex: 1,
    marginLeft: 10,
    color: colors.text,
  },
  searchIconContainer: {
    width: ICON_SIZE,
    height: ICON_SIZE,
    marginLeft: 8,
  },
  legend: {
    position: "absolute",
    top: -10,
    left: 18,
    paddingHorizontal: 5,
  },
  errorMessage: {
    color: colors.aghRed,
    fontSize: 12,
    marginTop: 5,
    marginLeft: 10,
    height: 18,
  },
  errorMessageHidden: {
    height: 0,
    marginTop: 0,
  },
});

export default InputField;
