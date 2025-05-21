import { Ionicons } from "@expo/vector-icons";
import React, { useEffect, useState } from "react";
import {
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";

interface InputField {
  icon: React.ComponentProps<typeof Ionicons>["name"];
  placeholder: string;
  value: string;
  onChangeText: (text: string) => void;
  secureTextEntry?: boolean;
  toggleSecure?: () => void;
  keyboardType?:
    | "default"
    | "email-address"
    | "numeric"
    | "phone-pad"
    | "number-pad";
  errorMessage?: string;
  validate?: (text: string) => string | null; // Optional validation function
}

const InputField: React.FC<InputField> = ({
  icon,
  placeholder,
  value,
  onChangeText,
  secureTextEntry,
  toggleSecure,
  keyboardType = "default",
  errorMessage,
  validate,
}) => {
  const [showLegend, setShowLegend] = useState(true);
  const [showIcon, setShowIcon] = useState(true);
  const [localErrorMessage, setLocalErrorMessage] = useState<
    string | null | undefined
  >(null);
  const [isTouched, setIsTouched] = useState(false);

  useEffect(() => {
    setShowLegend(value === "");
    setShowIcon(value === "");
  }, [value]);

  const handleTextChange = (text: string) => {
    setShowLegend(text === "");
    setShowIcon(text === "");

    if (keyboardType === "email-address") {
      text = text.toLowerCase();
    }

    onChangeText(text);
  };

  const handleBlur = () => {
    setIsTouched(true);

    if (validate) {
      const validationError = validate(value);
      setLocalErrorMessage(validationError);
    } else if (errorMessage) {
      setLocalErrorMessage(errorMessage);
    }
  };

  const handleFocus = () => {
    // hide error when focusing on the input again
    setLocalErrorMessage(null);
  };

  const displayErrorMessage = isTouched && (localErrorMessage || errorMessage);

  return (
    <View style={styles.container}>
      <View
        style={[
          styles.inputBox,
          displayErrorMessage ? styles.inputBoxError : null,
        ]}
      >
        {!showLegend && <Text style={styles.legend}>{placeholder}</Text>}
        {showIcon && <Ionicons name={icon} size={20} color="#ff914d" />}
        <TextInput
          style={styles.input}
          placeholder={placeholder}
          value={value}
          onChangeText={handleTextChange}
          onBlur={handleBlur}
          onFocus={handleFocus}
          secureTextEntry={secureTextEntry}
          keyboardType={keyboardType}
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
      {displayErrorMessage && (
        <Text style={styles.errorMessage}>
          {localErrorMessage || errorMessage}
        </Text>
      )}
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
    left: 26,
    backgroundColor: "#f5f5f5",
    color: "#aaa",
    paddingHorizontal: 5,
  },
  errorMessage: {
    color: "red",
    marginTop: 5,
    marginLeft: 10,
  },
});

export default InputField;
