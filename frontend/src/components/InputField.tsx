import { Ionicons } from "@expo/vector-icons";
import React, { useState } from "react";
import {
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";

interface InputFieldProps {
  placeholder: string;
  value: string;
  onChangeText: (text: string) => void;
  secureTextEntry?: boolean;
  toggleSecure?: () => void;
  errorMessage?: string;
  validate?: (text: string) => string | null;
  autoCapitalize?: "none" | "sentences" | "words" | "characters";
}

const InputField: React.FC<InputFieldProps> = ({
  placeholder,
  value,
  onChangeText,
  secureTextEntry,
  toggleSecure,
  errorMessage,
  validate,
  autoCapitalize = "none",
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
        {!isEmpty && <Text style={styles.legend}>{placeholder}</Text>}
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
        />
        {toggleSecure && (
          <TouchableOpacity onPress={toggleSecure}>
            <Ionicons
              name={secureTextEntry ? "eye-off-outline" : "eye-outline"}
              size={20}
              color="#ff914d"
            />
          </TouchableOpacity>
        )}
      </View>

      <Text style={styles.errorMessage}>{displayErrorMessage}</Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    marginBottom: 15,
  },
  inputBox: {
    flexDirection: "row",
    alignItems: "center",
    borderRadius: 10,
    paddingHorizontal: 10,
    height: 50,
    borderWidth: 2,
    borderColor: "#ccc",
  },
  inputBoxError: {
    borderColor: "red",
  },
  input: {
    flex: 1,
    marginLeft: 10,
  },
  legend: {
    position: "absolute",
    top: -10,
    left: 18,
    backgroundColor: "#f5f5f5",
    color: "#aaa",
    paddingHorizontal: 5,
  },
  errorMessage: {
    color: "red",
    fontSize: 12,
    marginTop: 5,
    marginLeft: 10,
    height: 18,
  },
});

export default InputField;
