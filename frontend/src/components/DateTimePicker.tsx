import { TouchableOpacity, Text, View } from "react-native";
import React, { useState, useEffect } from "react";
import DateTimePickerNative, { DateTimePickerEvent } from "@react-native-community/datetimepicker";

interface DatePickerProps {
    onDateSelected: (date: string, time: string) => void;
    initialDate: Date;
    initialTime: Date;
}

const DatePicker: React.FC<DatePickerProps> = ({
    onDateSelected,
    initialDate,
    initialTime
}) => {

    // --- IMPORTANT CHANGE: Initialize state directly with props ---
    // This ensures the state is set *once* when the component mounts.
    const [eventDate, setEventDate] = useState(initialDate);
    const [eventTime, setEventTime] = useState(initialTime);
    // -------------------------------------------------------------

    const [showDatePicker, setShowDatePicker] = useState(false);
    const [showTimePicker, setShowTimePicker] = useState(false);

    const formatDate = (dateObj: Date): string => {
        const day = String(dateObj.getDate()).padStart(2, '0');
        const month = String(dateObj.getMonth() + 1).padStart(2, '0');
        const year = dateObj.getFullYear();
        return day + '.' + month + '.' + year;
    };

    const formatTime = (timeObj: Date): string => {
        const hours = String(timeObj.getHours()).padStart(2, '0');
        const minutes = String(timeObj.getMinutes()).padStart(2, '0');
        return hours + ':' + minutes;
    };

    useEffect(() => {
        const formattedDate = formatDate(eventDate);
        const formattedTime = formatTime(eventTime);
        onDateSelected(formattedDate, formattedTime);
    }, [eventDate, eventTime]);


    const onEventDateChange = (event: DateTimePickerEvent, selectedDate?: Date) => {
        const currentDate = selectedDate || eventDate;
        setShowDatePicker(false);
        setEventDate(currentDate);
    };

    const onTimeChange = (event: DateTimePickerEvent, selectedDate?: Date) => {
        const currentDate = selectedDate || eventTime;
        setShowTimePicker(false);
        setEventTime(currentDate);
    };

    return (
        <View style={{ flex: 1, justifyContent: 'center', flexDirection: "row" }}>
            <View style={{ marginHorizontal: 10 }}>
                <TouchableOpacity onPress={() => setShowDatePicker(true)} style={{ backgroundColor: '#045ddaff', paddingVertical: 10, borderRadius: 25, paddingHorizontal: 25 }}>
                    <Text style={{ color: '#ffffff' }}>Wybierz datę</Text>
                </TouchableOpacity>
                <Text style={{ color: '#000000', paddingVertical: 10, alignSelf: "center", fontWeight: "bold"}}>
                        {eventDate.toLocaleDateString('pl-PL')}
                </Text>
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
                <TouchableOpacity onPress={() => setShowTimePicker(true)} style={{ backgroundColor: '#045ddaff', paddingVertical: 10, borderRadius: 25, paddingHorizontal: 20 }}>
                    <Text style={{ color: '#ffffff' }}>Wybierz godzinę</Text>
                </TouchableOpacity>
                
                    <Text style={{ color: '#000000', paddingVertical: 10, alignSelf: "center", fontWeight: "bold"}}>
                        {eventTime.toLocaleTimeString('pl-PL', {
                            hour: '2-digit',
                            minute: '2-digit',
                            hour12: false
                        })}
                    </Text>
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