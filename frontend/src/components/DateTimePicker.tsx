import { Text, View } from "react-native";
import React, { useState, useEffect } from "react";
import DateTimePickerNative, {
  DateTimePickerEvent,
} from "@react-native-community/datetimepicker";
import Button from "./Button";
import { THEME } from "../utils/constants";
import { useTheme } from "../contexts/ThemeContext";
import { Platform } from "react-native";

interface DatePickerProps {
  onDateSelected: (date: string, time: string) => void;
  initialDate: Date;
  initialTime: Date;
}

const DatePicker: React.FC<DatePickerProps> = ({
  onDateSelected,
  initialDate,
  initialTime,
}) => {
  const { colors, isDark } = useTheme();

  const [eventDate, setEventDate] = useState(initialDate);
  const [eventTime, setEventTime] = useState(initialTime);

  const [showDatePicker, setShowDatePicker] = useState(false);
  const [showTimePicker, setShowTimePicker] = useState(false);

  const formatDate = (dateObj: Date): string => {
    const day = String(dateObj.getDate()).padStart(2, "0");
    const month = String(dateObj.getMonth() + 1).padStart(2, "0");
    const year = dateObj.getFullYear();
    return day + "." + month + "." + year;
  };

  const formatTime = (timeObj: Date): string => {
    const hours = String(timeObj.getHours()).padStart(2, "0");
    const minutes = String(timeObj.getMinutes()).padStart(2, "0");
    return hours + ":" + minutes;
  };

  useEffect(() => {
    const formattedDate = formatDate(eventDate);
    const formattedTime = formatTime(eventTime);
    onDateSelected(formattedDate, formattedTime);
  }, [eventDate, eventTime]);

  // those event props must be here as the datetime picker needs it to function
  const onEventDateChange = (
    event: DateTimePickerEvent,
    selectedDate?: Date,
  ) => {
    const currentDate = selectedDate || eventDate;
    setShowDatePicker(false);
    setEventDate(currentDate);
  };

  const onTimeChange = (event: DateTimePickerEvent, selectedDate?: Date) => {
    const currentDate = selectedDate || eventTime;
    setShowTimePicker(false);
    setEventTime(currentDate);
  };

  return Platform.OS === "ios" ? (
    <View style={{ flex: 1, justifyContent: "center", flexDirection: "row" }}>
      <View style={{ marginHorizontal: 10 }}>
        <DateTimePickerNative
          value={eventDate}
          mode="date"
          is24Hour={true}
          display="default"
          onChange={onEventDateChange}
          themeVariant={isDark ? "dark" : "light"}
        />
      </View>
      <View style={{ marginHorizontal: 10 }}>
        <DateTimePickerNative
          value={eventTime}
          mode="time"
          is24Hour={true}
          display="default"
          onChange={onTimeChange}
          themeVariant={isDark ? "dark" : "light"}
        />
      </View>
    </View>
  ) : (
    <View style={{ flex: 1, justifyContent: "center", flexDirection: "row" }}>
      <View style={{ marginHorizontal: 10 }}>
        <Button
          title={eventDate.toLocaleDateString("pl-PL")}
          onPress={() => setShowDatePicker(true)}
          style={{ width: "auto", marginVertical: 0, paddingHorizontal: 25 }}
          textStyle={{ color: colors.text }}
        />
        {showDatePicker && (
          <DateTimePickerNative
            value={eventDate}
            mode="date"
            is24Hour={true}
            display="default"
            onChange={onEventDateChange}
          />
        )}
      </View>
      <View style={{ marginHorizontal: 10 }}>
        <Button
          title={eventTime.toLocaleTimeString("pl-PL", {
            hour: "2-digit",
            minute: "2-digit",
            hour12: false,
          })}
          onPress={() => setShowTimePicker(true)}
          style={{ width: "auto", marginVertical: 0, paddingHorizontal: 20 }}
          textStyle={{ color: colors.text }}
        />

        {showTimePicker && (
          <DateTimePickerNative
            value={eventTime}
            mode="time"
            is24Hour={true}
            display="default"
            onChange={onTimeChange}
          />
        )}
      </View>
    </View>
  );
};

export default DatePicker;
