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
}) => {
  const [showLegend, setShowLegend] = useState(true);
  const [showError, setShowError] = useState(false);

  useEffect(() => {
    setShowLegend(value === "");
  }, [value]);

  const handleTextChange = (text: string) => {
    setShowLegend(text === "");
    console.log(text);

    if (keyboardType === "email-address") {
      text = text.toLowerCase();
    }

    onChangeText(text);
  };

  return (
    <View style={styles.inputBox}>
      {!showLegend && <Text style={styles.legend}>{placeholder}</Text>}
      {<Ionicons name={icon} size={20} color="#ff914d" />}
      <TextInput
        style={styles.input}
        placeholder={placeholder}
        value={value}
        onChangeText={handleTextChange}
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

      {showError && <Text style={styles.errorMessage}>{errorMessage}</Text>}
    </View>
  );
};

const styles = StyleSheet.create({
  inputBox: {
    flexDirection: "row",
    alignItems: "center",
    borderRadius: 10,
    paddingHorizontal: 10,
    height: 50,
    borderWidth: 2,
    borderColor: "#ccc",
  },
  input: {
    flex: 1,
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
    alignSelf: "flex-start",
  },
});

export default InputField;
