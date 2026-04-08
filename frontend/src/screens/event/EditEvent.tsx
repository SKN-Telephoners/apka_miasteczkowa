import React from "react";
import { View, Text, Alert, TextInput, SafeAreaView, ScrollView, Image, StyleSheet } from "react-native";
import { useEffect, useState } from "react";
import { useNavigation, useRoute } from "@react-navigation/native";
import { editEvent } from "../../services/events";
import DatePicker from "../../components/DateTimePicker";
import Checkbox from 'expo-checkbox';
import UserCard from "../../components/UserCard";
import api from "../../services/api";
import ItemSeparator from "../../components/ItemSeparator";
import Button from "../../components/Button";
import CollapsibleSection from "../../components/CollapsibleSection";
import { THEME } from "../../utils/constants";

const EditEvent = () => {
    const navigation = useNavigation<any>();
    const route = useRoute<any>();
    const { event } = route.params;

    const parseBoolean = (value: unknown): boolean => {
        if (typeof value === "boolean") return value;
        if (typeof value === "number") return value === 1;
        if (typeof value === "string") {
            const normalized = value.trim().toLowerCase();
            return ["true", "1", "t", "y", "yes"].includes(normalized);
        }
        return false;
    };

    const initialIsPrivate = parseBoolean(event?.is_private ?? event?.private ?? event?.isPrivate);

    const getInitialDateTime = () => {
        try {
            if (event.date && event.time) {
                const [day, month, year] = event.date.split('.').map(Number);
                const [hours, minutes] = event.time.split(':').map(Number);
                
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

    const initialValues = getInitialDateTime();

    const [title, setTitle] = useState(event.name || "");
    const [description, setDescription] = useState(event.description || "");
    const [location, setLocation] = useState(event.location || "");
    const [date, setDate] = useState(event.date || ""); 
    const [time, setTime] = useState(event.time || "");
    const [isPrivate, setIsPrivate] = useState<boolean>(initialIsPrivate);
    const [currentUsername, setCurrentUsername] = useState("użytkownik");
    const DESCRIPTION_LINE_HEIGHT = 20;
    const DESCRIPTION_MIN_HEIGHT = DESCRIPTION_LINE_HEIGHT * 5 + 20;
    const [descriptionInputHeight, setDescriptionInputHeight] = useState(DESCRIPTION_MIN_HEIGHT);

    const [dateObj, setDateObj] = useState<Date>(initialValues.date); 
    const [timeObj, setTimeObj] = useState<Date>(initialValues.time); 

    const [titleError, setTitleError] = useState("");
    const [locationError, setLocationError] = useState("");

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

        const [day, month, year] = date.split('.').map(Number);
        const [hours, minutes] = time.split(':').map(Number);

        if ([day, month, year, hours, minutes].some(Number.isNaN)) {
            return "Nieprawidłowy format daty lub godziny";
        }

        const selectedDateTime = new Date(year, month - 1, day, hours, minutes);
        const now = new Date();
        if (selectedDateTime <= now) return "Data i godzina muszą być w przyszłości";
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
            return false;
        }
        return !titleValidation && !locationValidation && !descriptionValidation;
    };

    const submitEditEvent = async () => {
        if (!validateInputs()) return;
        try {
            const eventId = event?.id || event?.event_id;

            if (!eventId) {
                Alert.alert("Błąd", "Brak identyfikatora wydarzenia.");
                return;
            }

            await editEvent(eventId, {
                name: title,
                description: description,
                date: date,
                time: time,
                location: location,
                is_private: isPrivate,
            });
            Alert.alert("Sukces", "Edytowano wydarzenie", [
                {
                    text: "OK",
                    onPress: () => navigation.navigate("EventScreen"),
                },
            ]);
        } catch (error: any) {
            const msg = error?.message || "Wystąpił nieoczekiwany błąd.";
            Alert.alert("Błąd edycji", msg);
        }
    };

    const handleEditEvent = () => {
        if (initialIsPrivate && !isPrivate) {
            Alert.alert(
                "Zmienić widoczność wydarzenia?",
                "To zmieni wydarzenie z prywatnego na publiczne. Czy chcesz kontynuować?",
                [
                    { text: "Anuluj", style: "cancel" },
                    { text: "Zmień", onPress: () => { submitEditEvent(); }, style: "destructive" },
                ]
            );
            return;
        }

        submitEditEvent();
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

                    <CollapsibleSection title="Lokalizacja" initialExpanded={true} style={{ padding: 10 }}>
                        <View style={{ flexDirection: "row" }}>
                            <Image source={require("../../../assets/map_selection.jpg")} />
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

                    <CollapsibleSection title="Data i czas" initialExpanded={true} style={{ padding: 10 }}>
                        <DatePicker
                            onDateSelected={handleDateTimeSelected}
                            initialDate={dateObj}
                            initialTime={timeObj}
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

                    <Button onPress={handleEditEvent} title="Edytuj"></Button>
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
        marginVertical: 10,
        borderRadius: 16,
    },
    photoPlaceholderButton: {
        position: "relative",
        borderRadius: 16,
        overflow: "hidden",
        marginHorizontal: 10,
        marginVertical: 10,
    },
    photoOverlay: {
        position: "absolute",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        justifyContent: "center",
        alignItems: "center",
        backgroundColor: "rgba(0, 0, 0, 0.28)",
        paddingHorizontal: 20,
    },
    photoOverlayTitle: {
        color: "#fff",
        fontSize: 18,
        fontWeight: "700",
        textAlign: "center",
    },
    photoOverlaySubtitle: {
        color: "#fff",
        marginTop: 6,
        textAlign: "center",
    },
    photoPlaceholderContent: {
        height: 250,
        width: 370,
        alignItems: "center",
        justifyContent: "center",
        backgroundColor: THEME.colors.lm_ico,
        borderRadius: 16,
        marginHorizontal: 10,
        marginVertical: 10,
    },
    photoPlaceholderTitle: {
        marginTop: 10,
        fontWeight: "700",
        color: THEME.colors.lm_txt,
    },
});

export default EditEvent;