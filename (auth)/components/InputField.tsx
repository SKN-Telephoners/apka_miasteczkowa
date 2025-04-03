import { Ionicons } from "@expo/vector-icons";
import React from "react";
import { StyleSheet, TextInput, View, TouchableOpacity } from "react-native";

interface InputField {
  icon: string;
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
}

const InputField: React.FC<InputField> = ({
  icon,
  placeholder,
  value,
  onChangeText,
  secureTextEntry,
  toggleSecure,
  keyboardType = "default",
}) => {
  return (
    <View style={styles.inputBox}>
      <Ionicons name="person-outline" size={20} color="#ff914d" />
      <TextInput
        placeholder={placeholder}
        value={value}
        onChangeText={onChangeText}
        secureTextEntry={secureTextEntry}
        style={styles.input}
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
  );
};

const styles = StyleSheet.create({
  inputBox: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#fff",
    borderRadius: 10,
    paddingHorizontal: 10,
    height: 50,
    borderWidth: 1,
    borderColor: "#ccc",
  },
  input: {
    flex: 1,
    marginLeft: 10,
  },
  errorMessage: {
    color: "red",
    marginTop: 5,
    marginLeft: 10,
    alignSelf: "flex-start",
  },
});

export default InputField;
