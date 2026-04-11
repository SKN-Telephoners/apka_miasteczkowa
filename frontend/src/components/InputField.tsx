import { Ionicons } from "@expo/vector-icons";
import React, { useState } from "react";
import {
  Image,
  TextStyle,
  TextInputProps,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import { THEME } from '../utils/constants';

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
const IMAGE_WIDTH = 90;
const IMAGE_HEIGHT = 90;
const SPRITE_SCALE = ICON_SIZE / BASE_TILE_SIZE;

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
              { color: floatingLabelColor, backgroundColor: floatingLabelBackgroundColor },
            ]}
          >
            {placeholder}
          </Text>
        )}
        <TextInput
          style={styles.input}
          placeholder={placeholder}
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
              color={THEME.colors.light.transparentHighlight}
            />
          </TouchableOpacity>
        )}
        {!toggleSecure && showSearchSpriteIcon && (
          <View style={styles.searchIconContainer}>
            <Image
              source={require("../../assets/iconset1.jpg")}
              style={styles.searchIconImage}
              resizeMode="cover"
            />
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

const styles = StyleSheet.create({
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
    borderColor: THEME.colors.light.searchWord,
    backgroundColor: THEME.colors.light.searchWord
  },
  inputBoxError: {
    borderColor: THEME.colors.light.aghRed,
  },
  input: {
    flex: 1,
    marginLeft: 10,
  },
  searchIconContainer: {
    width: ICON_SIZE,
    height: ICON_SIZE,
    overflow: "hidden",
    marginLeft: 8,
  },
  searchIconImage: {
    width: IMAGE_WIDTH * SPRITE_SCALE,
    height: IMAGE_HEIGHT * SPRITE_SCALE,
    transform: [{ translateX: 0 }, { translateY: 0 }],
  },
  legend: {
    position: "absolute",
    top: -10,
    left: 18,
    paddingHorizontal: 5,
  },
  errorMessage: {
    color: THEME.colors.light.aghRed,
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
