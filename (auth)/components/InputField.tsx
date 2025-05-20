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
  const handleTextChange = (text: string) => {
    if (keyboardType === "email-address") {
      text = text.toLowerCase();
    }
    onChangeText(text);
  };

  return (
    <View style={styles.inputContainer}>
      <View style={styles.inputBox}>
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
      </View>
      
      {errorMessage ? <Text style={styles.errorMessage}>{errorMessage}</Text> : null}
    </View>
  );
};

const styles = StyleSheet.create({
  inputContainer: {
    marginBottom: 30,
    position: 'relative',
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
  input: {
    flex: 1,
  },
  errorMessage: {
    position: "absolute",
    bottom: -25,
    left: 10,
    color: "#f00",
    fontSize: 12,
  },
});

export default InputField;