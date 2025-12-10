import React from "react";
import { View, TouchableOpacity, Text, Alert } from "react-native";
import { useState, useEffect } from "react";
import { useRoute } from "@react-navigation/native";
import InputField from "../../components/InputField";
import { createEvent } from "../../services/events";
import DatePicker from "../../components/DateTimePicker";

const EditEvent = () => {
    const route = useRoute<any>();
    const { event } = route.params;

    const parseEventDateTime = () => {
        try {

            
            if (event.date && event.time) {
                const [day, month, year] = event.date.split('.').map(Number);
                const [hours, minutes] = event.time.split(':').map(Number);
                
    
                
                const dateObj = new Date(year, month - 1, day);
                const timeObj = new Date(year, month - 1, day, hours, minutes);
                
                console.log("Created Date objects:", dateObj, timeObj);
                
                return {
                    date: dateObj,
                    time: timeObj
                };
            }
        } catch (error) {
            console.error("Error parsing event date/time:", error);
        }
        

        const now = new Date();
        console.log("Using fallback date:", now);
        return {
            date: now,
            time: now
        };
    };

    const [title, setTitle] = useState(event.name || "");
    const [description, setDescription] = useState(event.description || "");
    const [location, setLocation] = useState(event.location || "");
    const [date, setDate] = useState(event.date || ""); 
    const [time, setTime] = useState(event.time || "");
    const [dateObj, setDateObj] = useState<Date>(new Date()); 
    const [timeObj, setTimeObj] = useState<Date>(new Date()); 

    const [titleError, setTitleError] = useState("");
    const [locationError, setLocationError] = useState("");


    useEffect(() => {
        const { date: initialDate, time: initialTime } = parseEventDateTime();
        setDateObj(initialDate);
        setTimeObj(initialTime);
    }, []);

    const validateTitle = (text: string): string | null => {
    if (!text) {
      return "Pole tytuł jest wymagane";
    }

    if (text.length < 3 || text.length > 32) {
      return "Tytuł musi mieć 3-32 znaków";
    }

    return null;
  };

  const validateLocation = (text: string): string | null => {
    if (!text) {
      return "Pole lokalizacja jest wymagane";
    }

    if (text.length < 3 || text.length > 32) {
      return "Lokalizacja może mieć maksymalnie 32 znaki";
    }

    return null;
  };

  const validateDescription = (text: string): string | null => {
    if (text.length > 1000) {
      return "Opis może mieć makysmalnie 1000 znaków";
    }

    return null;
  };

    const validateDateTime = (date: string, time: string): string | null => {
        if (!date || !time) {
            return "Pole data i czas są wymagane";
        }

        try {
            const [day, month, year] = date.split('.').map(Number);
            const [hours, minutes] = time.split(':').map(Number);

            const selectedDateTime = new Date(year, month - 1, day, hours, minutes);
            const now = new Date();

            if (selectedDateTime <= now) {
                return "Data i godzina muszą być w przyszłości";
            }
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
        if (!validateInputs()) {
            return;
        }
        try {
            console.log("Sending data to API:", {
                name: title,
                description: description,
                date: date,
                time: time,
                location: location
            });

            await createEvent({
                name: title,
                description: description,
                date: date,
                time: time,
                location: location
            });
            Alert.alert("Sukces", "Edytowano wydarzenie");
        } catch (error: any) {
            if (error.response) {
                Alert.alert(
                    "Edycja wydarzenia się nie powiodła",
                    error.response.data.message
                );
            } else {
                Alert.alert(
                    "Błąd edycji wydarzenia",
                    "Wystąpił nieoczekiwany błąd. Spróbuj ponownie."
                );
            }
        }
    };

    const handleDateTimeSelected = (selectedDate: string, selectedTime: string) => {
        console.log("Date selected:", selectedDate, "Time selected:", selectedTime);
        setDate(selectedDate);
        setTime(selectedTime);
        
        try {
            const [day, month, year] = selectedDate.split('.').map(Number);
            const [hours, minutes] = selectedTime.split(':').map(Number);
            
            const newDateObj = new Date(year, month - 1, day);
            const newTimeObj = new Date(year, month - 1, day, hours, minutes);
            
            setDateObj(newDateObj);
            setTimeObj(newTimeObj);
            
            console.log("Updated date objects:", newDateObj, newTimeObj);
        } catch (error) {
            console.error("Error updating date objects:", error);
        }
    };

    return (
        <View style={{ flex: 1, padding: 10, marginVertical: 10 }}>
            <InputField
                placeholder="Tytuł"
                errorMessage={titleError}
                onChangeText={setTitle}
                value={title} />

            <InputField
                placeholder="Opis"
                onChangeText={setDescription}
                value={description} />

            <InputField
                placeholder="Lokalizacja"
                errorMessage={locationError}
                onChangeText={setLocation}
                value={location} />

            <DatePicker
                onDateSelected={handleDateTimeSelected}
                initialDate={dateObj}
                initialTime={timeObj}
            />

            <TouchableOpacity 
                onPress={handleEditEvent} 
                style={{ 
                    backgroundColor: '#045ddaff', 
                    alignItems: 'center', 
                    padding: 15, 
                    borderRadius: 25,
                    marginTop: 20 
                }} 
            >
                <Text style={{ color: '#ffffff', fontSize: 16, fontWeight: 'bold' }}>Edytuj</Text>
            </TouchableOpacity>
        </View>
    );
};

export default EditEvent;