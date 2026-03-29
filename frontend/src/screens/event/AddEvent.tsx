import React from "react";
import { View, Text, Alert, StyleSheet, SafeAreaView, Image, ScrollView } from "react-native";
import { useEffect, useState } from "react";
import { createEvent } from "../../services/events";
import DatePicker from "../../components/DateTimePicker";
import Checkbox from 'expo-checkbox';
import UserCard from "../../components/UserCard";
import api from "../../services/api";
import { THEME } from "../../utils/constants";
import { TextInput } from "react-native";
import ItemSeparator from "../../components/ItemSeparator";
import Button from "../../components/Button";
import CollapsibleSection from "../../components/CollapsibleSection";
import { useNavigation } from "@react-navigation/native";


const AddEvent = () => {
  const navigation = useNavigation<any>();


  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [location, setLocation] = useState("");
  const [date, setDate] = useState("");
  const [time, setTime] = useState("");
  const [isPrivate, setIsPrivate] = useState(false);
  const [currentUsername, setCurrentUsername] = useState("użytkownik");
  const DESCRIPTION_LINE_HEIGHT = 20;
  const DESCRIPTION_MIN_HEIGHT = DESCRIPTION_LINE_HEIGHT * 5 + 20;
  const [descriptionInputHeight, setDescriptionInputHeight] = useState(DESCRIPTION_MIN_HEIGHT);

  useEffect(() => {
    const loadCurrentUser = async () => {
      try {
        const response = await api.get("/api/users/me");
        const username = response?.data?.user?.username;
        if (typeof username === "string" && username.trim()) {
          setCurrentUsername(username.trim());
        }
      } catch {
        setCurrentUsername("użytkownik");
      }
    };

    loadCurrentUser();
  }, []);

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

    if ([day, month, year, hours, minutes].some(Number.isNaN)) {
      return "Nieprawidłowy format daty lub godziny";
    }

    const selectedDateTime = new Date(year, month - 1, day, hours, minutes);

    const now = new Date();

    if (selectedDateTime <= now) {
      return "Data i godzina muszą być w przyszłości";
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

    if (dateTimeValidation) {
      Alert.alert("Błąd", dateTimeValidation);
    }

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
          location: location,
          is_private: isPrivate,
        }
      );
      setTitle("");
      setDescription("");
      setLocation("");
      setDate("");
      setTime("");
      setIsPrivate(false);
      setTitleError("");
      setLocationError("");

      Alert.alert("Dodano wydarzenie", "", [
        {
          text: "OK",
          onPress: () => navigation.navigate("EventScreen"),
        },
      ]);
      return;
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

  };

  const handleDateTimeSelected = (selectedDate: string, selectedTime: string) => {
    setDate(selectedDate);
    setTime(selectedTime);
  };

  return (
    <SafeAreaView style={styles.screen}>
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.container}>
          <UserCard
            creatorDisplayName={currentUsername}
            showCreatedAt={false}
            showMetaIcon={false}
          />
          <TextInput
            placeholder="Dodaj tytuł... "
            placeholderTextColor={THEME.colors.lm_ico}
            style={styles.titleInput}
            value={title}
            onChangeText={setTitle}
          ></TextInput>
          {titleError ? <Text style={styles.errorText}>{titleError}</Text> : null}
          <Image source={require("../../../assets/photo_icon.jpg")} style={styles.photo} />
          <TextInput
            placeholder="Dodaj tekst... "
            style={[styles.textInput, styles.descriptionInput, { height: descriptionInputHeight }]}
            numberOfLines={5}
            multiline
            value={description}
            onChangeText={setDescription}
            onContentSizeChange={(event) => {
              const contentHeight = event.nativeEvent.contentSize.height;
              setDescriptionInputHeight(Math.max(DESCRIPTION_MIN_HEIGHT, contentHeight));
            }}
          ></TextInput>
          <ItemSeparator></ItemSeparator>
          <CollapsibleSection title="Lokalizacja" initialExpanded={true} style={{padding: 10}}>
            <View style={{flexDirection: "row"}}>
              <Image source={require("../../../assets/map_selection.jpg")}/>
              <View>
              <Text style={styles.nameInput}>Nazwa</Text>
              <TextInput
                placeholder="Wpisz nazwę..."
                placeholderTextColor={THEME.colors.lm_ico}
                style={styles.textInput}
                value={location}
                onChangeText={setLocation}
              />
              {locationError ? <Text style={styles.errorText}>{locationError}</Text> : null}
            </View>
            </View>
          </CollapsibleSection>

          <ItemSeparator></ItemSeparator>

          <CollapsibleSection title="Data i czas" initialExpanded={true} style={{padding: 10}}>
          <DatePicker
            onDateSelected={handleDateTimeSelected}
            initialDate={new Date()}
            initialTime={new Date()}
          />
          </CollapsibleSection>

          <ItemSeparator></ItemSeparator>
          <View style={{ flexDirection: "row", marginVertical: 10, padding: 10 }}>
            <Checkbox
              value={isPrivate}
              onValueChange={setIsPrivate}
              color={isPrivate ? THEME.colors.lm_highlight : undefined}
            />
            <Text style={{ marginLeft: 10 }}>Wydarzenie prywatne</Text>
          </View>

          <Button onPress={handleCreateEvent} title="Opublikuj">
          </Button>

        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: THEME.colors.lm_bg,
  },
  scrollView: {
    flex: 1,
    backgroundColor: THEME.colors.lm_bg,
  },
  scrollContent: {
    paddingBottom: 24,
    backgroundColor: THEME.colors.lm_bg,
  },
  container: {
    paddingLeft: 10,
    paddingRight: 10,
    paddingTop: 10,
    paddingBottom: 10,
    backgroundColor: THEME.colors.lm_bg,
  },
  titleInput: {
    paddingBottom: 10,
    paddingTop: 25,
    padding: 10,
    ...THEME.typography.title,
    fontWeight: "700",
    color: THEME.colors.lm_ico,
  },

  nameInput: {
    paddingBottom: 10,
    paddingTop: 25,
    padding: 10,
    ...THEME.typography.title,
    fontWeight: "700",
    color: THEME.colors.lm_txt,
  },

  textInput: {
    padding: 10,
  },
  descriptionInput: {
    textAlignVertical: "top",
  },
  errorText: {
    color: THEME.colors.agh_red,
    fontSize: 12,
    marginTop: 4,
    marginLeft: 10,
  },
  photo: {
    height: 250,
    width: 370,
    padding: 10,
    marginHorizontal: 10,
    marginVertical: 10
  }
});

export default AddEvent;
