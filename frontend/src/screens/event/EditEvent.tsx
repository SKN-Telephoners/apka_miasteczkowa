import React from "react";
import { View, TouchableOpacity, Text, Alert } from "react-native";
import { useState } from "react"; 
import { useRoute } from "@react-navigation/native";
import InputField from "../../components/InputField";
import { createEvent } from "../../services/events";
import DatePicker from "../../components/DateTimePicker";

const EditEvent = () => {
    const route = useRoute<any>();
    const { event } = route.params;

    // Helper function moved here so it can be used during state initialization
    const getInitialDateTime = () => {
        try {
            if (event.date && event.time) {
                const [day, month, year] = event.date.split('.').map(Number);
                const [hours, minutes] = event.time.split(':').map(Number);
                
                // JavaScript Date: months are 0-indexed (0 = Jan, 11 = Dec)
                const dateObj = new Date(year, month - 1, day);
                const timeObj = new Date(year, month - 1, day, hours, minutes);
                
                return { date: dateObj, time: timeObj };
            }
        } catch (error) {
            console.error("Error parsing event date/time:", error);
        }
        
        const now = new Date();
        return { date: now, time: now };
    };

    // Calculate these ONCE immediately, before the render happens
    const initialValues = getInitialDateTime();

    const [title, setTitle] = useState(event.name || "");
    const [description, setDescription] = useState(event.description || "");
    const [location, setLocation] = useState(event.location || "");
    const [date, setDate] = useState(event.date || ""); 
    const [time, setTime] = useState(event.time || "");

    const [dateObj, setDateObj] = useState<Date>(initialValues.date); 
    const [timeObj, setTimeObj] = useState<Date>(initialValues.time); 

    const [titleError, setTitleError] = useState("");
    const [locationError, setLocationError] = useState("");

    const validateTitle = (text: string): string | null => {
        if (!text) return "Pole tytuł jest wymagane";
        if (text.length < 3 || text.length > 32) return "Tytuł musi mieć 3-32 znaków";
        return null;
    };

    const validateLocation = (text: string): string | null => {
        if (!text) return "Pole lokalizacja jest wymagane";
        if (text.length < 3 || text.length > 32) return "Lokalizacja może mieć maksymalnie 32 znaki";
        return null;
    };

    const validateDescription = (text: string): string | null => {
        if (text.length > 1000) return "Opis może mieć makysmalnie 1000 znaków";
        return null;
    };

    const validateDateTime = (date: string, time: string): string | null => {
        if (!date || !time) return "Pole data i czas są wymagane";
        try {
            const [day, month, year] = date.split('.').map(Number);
            const [hours, minutes] = time.split(':').map(Number);
            const selectedDateTime = new Date(year, month - 1, day, hours, minutes);
            const now = new Date();
            if (selectedDateTime <= now) return "Data i godzina muszą być w przyszłości";
            return null;
        } catch (error) {
            return "Nieprawidłowy format daty lub czasu";
        }
    };

    const validateInputs = () => {
        const titleValidation = validateTitle(title);
        const locationValidation = validateLocation(location);
        const descriptionValidation = validateDescription(description);
        const dateTimeValidation = validateDateTime(date, time);

        setTitleError(titleValidation || "");
        setLocationError(locationValidation || "");

        if (dateTimeValidation) {
            Alert.alert("Błąd", dateTimeValidation);
            return false;
        }
        return !titleValidation && !locationValidation && !descriptionValidation;
    };

    const handleEditEvent = async () => {
        if (!validateInputs()) return;
        try {
            await createEvent({
                name: title,
                description: description,
                date: date,
                time: time,
                location: location
            });
            Alert.alert("Sukces", "Edytowano wydarzenie");
        } catch (error: any) {
            const msg = error.response?.data?.message || "Wystąpił nieoczekiwany błąd.";
            Alert.alert("Błąd edycji", msg);
        }
    };

    const handleDateTimeSelected = (selectedDate: string, selectedTime: string) => {
        setDate(selectedDate);
        setTime(selectedTime);
        
        try {
            const [day, month, year] = selectedDate.split('.').map(Number);
            const [hours, minutes] = selectedTime.split(':').map(Number);
            
            setDateObj(new Date(year, month - 1, day));
            setTimeObj(new Date(year, month - 1, day, hours, minutes));
        } catch (error) {
            console.error("Error updating date objects:", error);
        }
    };

    return (
        <View style={{ flex: 1, padding: 10, marginVertical: 10 }}>
            <InputField placeholder="Tytuł" errorMessage={titleError} onChangeText={setTitle} value={title} />
            <InputField placeholder="Opis" onChangeText={setDescription} value={description} />
            <InputField placeholder="Lokalizacja" errorMessage={locationError} onChangeText={setLocation} value={location} />

            <DatePicker
                onDateSelected={handleDateTimeSelected}
                initialDate={dateObj}
                initialTime={timeObj}
            />

            <TouchableOpacity 
                onPress={handleEditEvent} 
                style={{ backgroundColor: '#045ddaff', alignItems: 'center', padding: 15, borderRadius: 25, marginTop: 20 }} 
            >
                <Text style={{ color: '#ffffff', fontSize: 16, fontWeight: 'bold' }}>Edytuj</Text>
            </TouchableOpacity>
        </View>
    );
};

export default EditEvent;