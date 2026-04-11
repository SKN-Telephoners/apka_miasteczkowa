import React from "react";
import { View, Text, Alert, TextInput, SafeAreaView, ScrollView, Image, StyleSheet, TouchableOpacity, ActivityIndicator } from "react-native";
import { useEffect, useLayoutEffect, useMemo, useState } from "react";
import { useNavigation, useRoute } from "@react-navigation/native";
import { editEvent, uploadEventPicture } from "../../services/events";
import DatePicker from "../../components/DateTimePicker";
import Checkbox from 'expo-checkbox';
import UserCard from "../../components/UserCard";
import api from "../../services/api";
import ItemSeparator from "../../components/ItemSeparator";
import Button from "../../components/Button";
import CollapsibleSection from "../../components/CollapsibleSection";
import { THEME } from "../../utils/constants";
import * as ImagePicker from "expo-image-picker";
import * as FileSystem from "expo-file-system";
import { EventPicture } from "../../types";
import { buildEventPreview } from "../../utils/eventPreview";
import SvgSpriteIcon from "../../components/SvgSpriteIcon";
import { useTheme } from "../../contexts/ThemeContext";

const EditEvent = () => {
    const navigation = useNavigation<any>();
    const route = useRoute<any>();
    const { event } = route.params;
    const { colors } = useTheme();
    const PREVIEW_ICON_SIZE = 22;
    const PREVIEW_ICON_OFFSET = { x: 0, y: -60 };

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
    const [eventPicture, setEventPicture] = useState<EventPicture | null>(event?.pictures?.[0] ?? null);
    const [eventPicturePreviewUri, setEventPicturePreviewUri] = useState<string | null>(event?.pictures?.[0]?.url ?? null);
    const [isPictureUploading, setIsPictureUploading] = useState(false);
    const DESCRIPTION_LINE_HEIGHT = 20;
    const DESCRIPTION_MIN_HEIGHT = DESCRIPTION_LINE_HEIGHT * 5 + 20;
    const [descriptionInputHeight, setDescriptionInputHeight] = useState(DESCRIPTION_MIN_HEIGHT);

    const [dateObj, setDateObj] = useState<Date>(initialValues.date); 
    const [timeObj, setTimeObj] = useState<Date>(initialValues.time); 

    const [titleError, setTitleError] = useState("");
    const [locationError, setLocationError] = useState("");
    const styles = useMemo(() => getStyles(colors), [colors]);

    const previewEvent = useMemo(() => {
        return buildEventPreview({
            title,
            description,
            location,
            date,
            time,
            isPrivate,
            creatorId: String(event?.creator_id ?? "preview-user"),
            creatorUsername: currentUsername,
            picture: eventPicture,
            pictureUri: eventPicturePreviewUri,
            id: String(event?.id ?? event?.event_id ?? "preview-event"),
        });
    }, [title, description, location, date, time, isPrivate, currentUsername, eventPicture, eventPicturePreviewUri, event?.creator_id, event?.id, event?.event_id]);

    useLayoutEffect(() => {
        navigation.setOptions({
            headerRight: () => (
                <TouchableOpacity
                    onPress={() => navigation.navigate("EventPreview", { event: previewEvent })}
                    style={{ marginRight: 16, width: PREVIEW_ICON_SIZE, height: PREVIEW_ICON_SIZE, overflow: "hidden" }}
                    activeOpacity={0.8}
                    accessibilityLabel="Podgląd"
                >
                    <SvgSpriteIcon set={2} size={PREVIEW_ICON_SIZE} offsetX={PREVIEW_ICON_OFFSET.x} offsetY={PREVIEW_ICON_OFFSET.y} />
                </TouchableOpacity>
            ),
        });
    }, [navigation, previewEvent]);

    const uploadSelectedPicture = async (asset: ImagePicker.ImagePickerAsset) => {
        if (!asset.uri) {
            Alert.alert("Błąd", "Nie udało się odczytać zdjęcia.");
            return;
        }

        const fileInfo = await FileSystem.getInfoAsync(asset.uri);
        const maxBytes = 15 * 1024 * 1024;
        if (fileInfo.exists && typeof fileInfo.size === "number" && fileInfo.size > maxBytes) {
            Alert.alert("Plik za duży", "Wybierz zdjęcie mniejsze niż 15 MB.");
            return;
        }

        setEventPicturePreviewUri(asset.uri);
        setIsPictureUploading(true);
        try {
            const uploadedPicture = await uploadEventPicture(asset.uri, asset.fileName ?? "event-picture.jpg");
            setEventPicture({ ...uploadedPicture, url: uploadedPicture.url ?? asset.uri });
        } catch (error: any) {
            setEventPicturePreviewUri(null);
            Alert.alert("Błąd zdjęcia", error?.message || "Nie udało się przesłać zdjęcia.");
        } finally {
            setIsPictureUploading(false);
        }
    };

    const takePhoto = async () => {
        const permission = await ImagePicker.requestCameraPermissionsAsync();
        if (!permission.granted) {
            Alert.alert("Brak uprawnień", "Aplikacja potrzebuje dostępu do aparatu.");
            return;
        }

        const result = await ImagePicker.launchCameraAsync({
            mediaTypes: ["images"],
            quality: 0.6,
            allowsEditing: true,
        });

        if (!result.canceled && result.assets?.[0]) {
            await uploadSelectedPicture(result.assets[0]);
        }
    };

    const pickFromDevice = async () => {
        const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
        if (!permission.granted) {
            Alert.alert("Brak uprawnień", "Aplikacja potrzebuje dostępu do galerii.");
            return;
        }

        const result = await ImagePicker.launchImageLibraryAsync({
            mediaTypes: ["images"],
            quality: 0.6,
            allowsEditing: true,
        });

        if (!result.canceled && result.assets?.[0]) {
            await uploadSelectedPicture(result.assets[0]);
        }
    };

    const showPictureOptions = () => {
        Alert.alert("Zdjęcie wydarzenia", "Wybierz źródło zdjęcia", [
            { text: "Zrób zdjęcie", onPress: takePhoto },
            { text: "Wybierz z urządzenia", onPress: pickFromDevice },
            eventPicture
                ? {
                    text: "Usuń zdjęcie",
                    style: "destructive",
                    onPress: () => {
                        setEventPicture(null);
                        setEventPicturePreviewUri(null);
                    },
                }
                : undefined,
            { text: "Anuluj", style: "cancel" },
        ].filter(Boolean) as any);
    };

    useEffect(() => {
        const loadCurrentUser = async () => {
            try {
                const response = await api.get("/api/users/profile");
                const username = response?.data?.username;
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
        if (isPictureUploading) {
            Alert.alert("Poczekaj", "Trwa przesyłanie zdjęcia. Spróbuj ponownie za chwilę.");
            return;
        }

        if (eventPicture && !eventPicture.cloud_id) {
            Alert.alert("Błąd zdjęcia", "Zdjęcie nie zostało poprawnie przesłane. Wybierz je ponownie.");
            return;
        }

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
                picture: eventPicture,
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
                        showUsernameIcon={false}
                    />
                    <TextInput
                        placeholder="Dodaj tytuł... "
                        placeholderTextColor={colors.searchWord}
                        style={styles.titleInput}
                        value={title}
                        onChangeText={setTitle}
                        autoComplete="off"
                        importantForAutofill="no"
                        autoCorrect={false}
                    ></TextInput>
                    {titleError ? <Text style={styles.errorText}>{titleError}</Text> : null}

                    <TouchableOpacity
                        style={styles.photoPlaceholderButton}
                        onPress={showPictureOptions}
                        activeOpacity={0.85}
                        disabled={isPictureUploading}
                    >
                        {isPictureUploading ? (
                            <View style={styles.photoPlaceholderContent}>
                                <ActivityIndicator size="large" color={colors.transparentHighlight} />
                                <Text style={styles.photoPlaceholderTitle}>Przesyłanie zdjęcia...</Text>
                            </View>
                        ) : (eventPicture?.url || eventPicturePreviewUri) ? (
                            <Image source={{ uri: eventPicture?.url ?? eventPicturePreviewUri! }} style={styles.photo} />
                        ) : (
                            <>
                                <Image source={require("../../../assets/photo_icon.jpg")} style={styles.photo} />
                                <View style={styles.photoOverlay}>
                                    <Text style={styles.photoOverlayTitle}>Dodaj zdjęcie</Text>
                                    <Text style={styles.photoOverlaySubtitle}>Zrób zdjęcie lub wybierz z urządzenia</Text>
                                </View>
                            </>
                        )}
                    </TouchableOpacity>

                    <TextInput
                        placeholder="Dodaj tekst... "
                        style={[styles.textInput, styles.descriptionInput, { height: descriptionInputHeight }]}
                        numberOfLines={5}
                        multiline
                        value={description}
                        onChangeText={setDescription}
                        autoComplete="off"
                        importantForAutofill="no"
                        autoCorrect={false}
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
                                    placeholderTextColor={colors.searchWord}
                                    style={styles.textInput}
                                    value={location}
                                    onChangeText={setLocation}
                                    autoComplete="off"
                                    importantForAutofill="no"
                                    autoCorrect={false}
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
                            color={isPrivate ? colors.transparentHighlight : undefined}
                        />
                        <Text style={{ marginLeft: 10, color: colors.text }}>Wydarzenie prywatne</Text>
                    </View>

                    <Button onPress={handleEditEvent} title={isPictureUploading ? "Przesyłanie zdjęcia..." : "Edytuj"} disabled={isPictureUploading}></Button>
                </View>
            </ScrollView>
        </SafeAreaView>
    );
};

const getStyles = (colors: typeof THEME.colors.light) => StyleSheet.create({
    screen: {
        flex: 1,
        backgroundColor: colors.background,
    },
    scrollView: {
        flex: 1,
        backgroundColor: colors.background,
    },
    scrollContent: {
        paddingBottom: 24,
        backgroundColor: colors.background,
    },
    container: {
        paddingLeft: 10,
        paddingRight: 10,
        paddingTop: 10,
        paddingBottom: 10,
        backgroundColor: colors.background,
    },
    titleInput: {
        paddingBottom: 10,
        paddingTop: 25,
        padding: 10,
        ...THEME.typography.title,
        fontWeight: "700",
        color: colors.text,
    },
    nameInput: {
        paddingBottom: 10,
        paddingTop: 25,
        padding: 10,
        ...THEME.typography.title,
        fontWeight: "700",
        color: colors.text,
    },
    textInput: {
        padding: 10,
        color: colors.text,
    },
    descriptionInput: {
        textAlignVertical: "top",
    },
    errorText: {
        color: colors.aghRed,
        fontSize: 12,
        marginTop: 4,
        marginLeft: 10,
    },
    photo: {
        height: 250,
        width: "100%",
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
        ...THEME.typography.eventTitle,
        color: "#fff",
        textAlign: "center",
    },
    photoOverlaySubtitle: {
        ...THEME.typography.text,
        color: "#fff",
        marginTop: 6,
        textAlign: "center",
    },
    photoPlaceholderContent: {
        height: 250,
        width: "100%",
        alignItems: "center",
        justifyContent: "center",
        backgroundColor: colors.border,
        borderRadius: 16,
    },
    photoPlaceholderTitle: {
        ...THEME.typography.text,
        marginTop: 10,
        fontWeight: "700",
        color: colors.text,
    },
});

export default EditEvent;