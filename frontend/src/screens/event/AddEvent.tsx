import React from "react";
import { View, TouchableOpacity, Text, Alert } from "react-native";
import { useState } from "react";
import InputField from "../../components/InputField";
import { createEvent } from "../../services/events";
import DatePicker from "../../components/DateTimePicker"


const AddEvent = () => {


  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [location, setLocation] = useState("");
  const [date, setDate] = useState("");
  const [time, setTime] = useState("");

  const [titleError, setTitleError] = useState("");
  const [locationError, setLocationError] = useState("");


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

    const [day, month, year] = date.split('.').map(Number);
    const [hours, minutes] = time.split(':').map(Number);

    const selectedDateTime = new Date(year, month - 1, day, hours, minutes);

    const now = new Date();

    if (selectedDateTime <= now) {
      Alert.alert("Data i godzina muszą być w przyszłości");
    }
    return null;
  };

  const validateInputs = () => {
    const titleValidation = validateTitle(title);
    const locationValidation = validateLocation(location);
    const descriptionValidation = validateDescription(description);
    const dateTimeValidation = validateDateTime(date, time);

    setTitleError(titleValidation || "");
    setLocationError(locationValidation || "");

    return (
      !titleValidation &&
      !locationValidation &&
      !dateTimeValidation &&
      !descriptionValidation
    );
  };

  const handleCreateEvent = async () => {
    if (!validateInputs()) {
      return;
    }
    try {
      await createEvent(
        {
          name: title,
          description: description,
          date: date,
          time: time,
          location: location
        }
      );
      Alert.alert("Dodano wydarzenie");
    } catch (error: any) {
      if (error.response) {
        Alert.alert(
          "Dodawanie wyddarzenia się nie powiodło",
          error.response.data.message
        );
      } else {
        Alert.alert(
          "Błąd dodawania wydarzenia",
          "Wystąpił nieoczekiwany błąd. Spróbuj ponownie."
        );
      }
    }

    setTitle("");
    setDescription("");
    setLocation("");
    setDate("");
    setTime("");
  };

  const handleDateTimeSelected = (selectedDate: string, selectedTime: string) => {
    setDate(selectedDate);
    setTime(selectedTime);
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
        initialDate={new Date()}
        initialTime={new Date()}
      />

      <TouchableOpacity onPress={handleCreateEvent} style={{ backgroundColor: '#045ddaff', alignItems: 'center', padding: 10, borderRadius: 25 }} >
        <Text style={{ color: '#ffffff' }}>Dodaj wydarzenie</Text>
      </TouchableOpacity>
    </View>
  );
};

export default AddEvent;
