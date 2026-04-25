import React from "react";
import { View, Text, Alert, StyleSheet, SafeAreaView, Image, ScrollView, TouchableOpacity, ActivityIndicator } from "react-native";
import { useEffect, useLayoutEffect, useMemo, useState } from "react";
import { createEvent, inviteToEvent, uploadEventPicture } from "../../services/events";
import DatePicker from "../../components/DateTimePicker";
import Checkbox from 'expo-checkbox';
import UserCard from "../../components/UserCard";
import { THEME } from "../../utils/constants";
import { TextInput } from "react-native";
import ItemSeparator from "../../components/ItemSeparator";
import Button from "../../components/Button";
import CollapsibleSection from "../../components/CollapsibleSection";
import { useNavigation, useRoute } from "@react-navigation/native";
import * as ImagePicker from "expo-image-picker";
import * as FileSystem from "expo-file-system";
import { EventPicture } from "../../types";
import { buildEventPreview } from "../../utils/eventPreview";
import AppIcon from "../../components/AppIcon";
import { useTheme } from "../../contexts/ThemeContext";
import { useUser } from "../../contexts/UserContext";
import { useFriends } from "../../contexts/FriendsContext";
import InputField from "../../components/InputField";

interface SelectedLocationParam {
  coordinates: [number, number];
  lat: number;
  lng: number;
  timestamp: number;
}


const AddEvent = () => {
  const navigation = useNavigation<any>();
  const route = useRoute<any>();
  const selectedLocation = route.params?.selectedLocation as SelectedLocationParam | undefined;
  const { colors } = useTheme();
  const { user: currentUser } = useUser();
  const PREVIEW_ICON_SIZE = 22;


  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [location, setLocation] = useState("");
  const [date, setDate] = useState("");
  const [time, setTime] = useState("");
  const [isPrivate, setIsPrivate] = useState(false);
  const [eventPicture, setEventPicture] = useState<EventPicture | null>(null);
  const [eventPicturePreviewUri, setEventPicturePreviewUri] = useState<string | null>(null);
  const [isPictureUploading, setIsPictureUploading] = useState(false);
  const { friends } = useFriends();
  const [searchQuery, setSearchQuery] = useState("");
  const [queuedInviteIds, setQueuedInviteIds] = useState<Record<string, boolean>>({});
  const DESCRIPTION_LINE_HEIGHT = 20;
  const DESCRIPTION_MIN_HEIGHT = DESCRIPTION_LINE_HEIGHT * 5 + 20;
  const [descriptionInputHeight, setDescriptionInputHeight] = useState(DESCRIPTION_MIN_HEIGHT);

  useEffect(() => {
    if (selectedLocation?.coordinates?.length === 2) {
      setLocation(JSON.stringify(selectedLocation.coordinates));
      setLocationError("");
      navigation.setParams?.({ selectedLocation: undefined });
    }
  }, [selectedLocation, navigation]);

  const previewEvent = useMemo(() => {
    const resolvedLocation = location || (selectedLocation?.coordinates ? JSON.stringify(selectedLocation.coordinates) : "");
    return buildEventPreview({
      title,
      description,
      location: resolvedLocation,
      date,
      time,
      isPrivate,
      creatorId: "preview-user",
      creatorUsername: currentUser?.username || "użytkownik",
      creatorProfilePictureUrl: currentUser?.profile_picture?.url || null,
      picture: eventPicture,
      pictureUri: eventPicturePreviewUri,
    });
  }, [title, description, location, selectedLocation, date, time, isPrivate, currentUser, eventPicture, eventPicturePreviewUri]);

  useLayoutEffect(() => {
    navigation.setOptions({
      headerRight: () => (
        <TouchableOpacity
          onPress={() => navigation.navigate("EventPreview", { event: previewEvent })}
            style={{ marginRight: 16, width: PREVIEW_ICON_SIZE, height: PREVIEW_ICON_SIZE, overflow: "hidden" }}
          activeOpacity={0.8}
            accessibilityLabel="Podgląd"
        >
            <AppIcon name="Preview" size={PREVIEW_ICON_SIZE} />
        </TouchableOpacity>
      ),
    });
  }, [navigation, previewEvent]);

  const [titleError, setTitleError] = useState("");
  const [locationError, setLocationError] = useState("");
  const styles = useMemo(() => getStyles(colors), [colors]);

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

    try {
      const parsed = JSON.parse(text);
      const isValid =
        Array.isArray(parsed) &&
        parsed.length === 2 &&
        typeof parsed[0] === "number" &&
        typeof parsed[1] === "number";
      if (!isValid) {
        return "Wybierz lokalizację na mapie";
      }
    } catch {
      return "Wybierz lokalizację na mapie";
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
    const resolvedLocation = location || (selectedLocation?.coordinates ? JSON.stringify(selectedLocation.coordinates) : "");
    const locationValidation = validateLocation(resolvedLocation);
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
    if (isPictureUploading) {
      Alert.alert("Poczekaj", "Trwa przesyłanie zdjęcia. Spróbuj ponownie za chwilę.");
      return;
    }

    if (eventPicture && !eventPicture.cloud_id) {
      Alert.alert("Błąd zdjęcia", "Zdjęcie nie zostało poprawnie przesłane. Wybierz je ponownie.");
      return;
    }

    if (!validateInputs()) {
      return;
    }
    try {
      const resolvedLocation = location || (selectedLocation?.coordinates ? JSON.stringify(selectedLocation.coordinates) : "");
      const createdEvent = await createEvent(
        {
          name: title,
          description: description,
          date: date,
          time: time,
          location: resolvedLocation,
          is_private: isPrivate,
          picture: eventPicture,
        }
      );

      const selectedInviteIds = Object.entries(queuedInviteIds)
        .filter(([, queued]) => queued)
        .map(([friendId]) => friendId);

      if (createdEvent?.event_id && selectedInviteIds.length > 0) {
        const inviteResults = await Promise.allSettled(
          selectedInviteIds.map((friendId) => inviteToEvent(createdEvent.event_id, friendId))
        );

        const failedInvites = inviteResults.filter((result) => result.status === "rejected").length;
        if (failedInvites > 0) {
          Alert.alert("Uwaga", `Wydarzenie utworzone, ale ${failedInvites} zaproszeń nie udało się wysłać.`);
        }
      }

      setTitle("");
      setDescription("");
      setLocation("");
      setDate("");
      setTime("");
      setIsPrivate(false);
      setEventPicture(null);
      setEventPicturePreviewUri(null);
      setSearchQuery("");
      setQueuedInviteIds({});
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

  const handleSearch = (text: string) => {
    setSearchQuery(text);
  };

  const toggleQueuedInvite = (friendId: string) => {
    setQueuedInviteIds((prev) => ({
      ...prev,
      [friendId]: !prev[friendId],
    }));
  };

  const filteredFriends = useMemo(() => {
    const normalizedQuery = searchQuery.trim().toLowerCase();
    if (!normalizedQuery) {
      return friends;
    }

    return friends.filter((friend) =>
      (friend.username || "").toLowerCase().includes(normalizedQuery)
    );
  }, [friends, searchQuery]);

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
            creatorDisplayName={currentUser?.username || "użytkownik"}
            avatarUri={currentUser?.profile_picture?.url ?? undefined}
            uniName={currentUser?.academy || undefined}
            majorName={currentUser?.course || undefined}
            yearOfStudy={currentUser?.year ?? undefined}
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
            <TouchableOpacity
              style={styles.mapPlaceholderButton}
              onPress={() => navigation.navigate("EventMap", { returnTo: "AddEvent", sourceRouteKey: route.key })}
              activeOpacity={0.85}
            >
              <Image source={require("../../../assets/map_selection.jpg")} style={styles.mapPlaceholderImage} />
              <View style={styles.mapPlaceholderOverlay}>
                <Text style={styles.mapPlaceholderTitle}>Wybierz lokalizację na mapie</Text>
                <Text style={styles.mapPlaceholderSubtitle}>
                  {location ? "Lokalizacja wybrana" : "Dotknij, aby wskazać miejsce"}
                </Text>
              </View>
            </TouchableOpacity>
            {locationError ? <Text style={styles.errorText}>{locationError}</Text> : null}
          </CollapsibleSection>

          <ItemSeparator></ItemSeparator>

          <CollapsibleSection title="Zaproś znajomych" initialExpanded={true} style={{ padding: 10 }}>
            <InputField
              placeholder="Szukaj znajomych..."
              value={searchQuery}
              onChangeText={handleSearch}
              showSearchSpriteIcon
              showFloatingLabel={false}
              reserveErrorSpace={false}
            />

            {filteredFriends.length > 0 ? (
              filteredFriends.map((friend) => {
                const friendId = String(friend?.id || "");
                const isQueued = Boolean(queuedInviteIds[friendId]);

                return (
                  <View key={friend.id} style={[styles.listItem, styles.friendRow, { borderColor: colors.border }]}> 
                    <View style={styles.friendInfo}>
                      <UserCard
                        creatorDisplayName={friend.username}
                        avatarUri={friend?.profile_picture?.url || friend?.avatarUrl || (typeof friend?.profile_picture === "string" ? friend?.profile_picture : undefined)}
                        createdAtDisplay=""
                        showCreatedAt={false}
                        showMetaIcon={false}
                        showUsernameIcon={false}
                        uniName={friend?.academy || undefined}
                        majorName={friend?.course || undefined}
                        yearOfStudy={friend?.year ?? undefined}
                        avatarSize={40}
                      />
                    </View>
                    <Button
                      title={isQueued ? "Wysłano" : "Zaproś"}
                      onPress={() => toggleQueuedInvite(friendId)}
                      style={styles.inviteButton}
                      textStyle={styles.inviteButtonText}
                    />
                  </View>
                );
              })
            ) : searchQuery.trim().length > 0 ? (
              <Text style={styles.infoText}>Brak znajomych pasujących do wyszukiwania</Text>
            ) : (
              <Text style={styles.infoText}>Brak znajomych na liście</Text>
            )}
          </CollapsibleSection>

          <ItemSeparator></ItemSeparator>

          <CollapsibleSection title="Data i czas" initialExpanded={true} style={{ padding: 10 }}>
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
              color={isPrivate ? colors.transparentHighlight : undefined}
            />
            <Text style={{ marginLeft: 10, color: colors.text }}>Wydarzenie prywatne</Text>
          </View>

          <Button onPress={handleCreateEvent} title={isPictureUploading ? "Przesyłanie zdjęcia..." : "Opublikuj"} disabled={isPictureUploading}>
          </Button>

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

  infoText: {
    ...THEME.typography.text,
    color: colors.icon,
    fontStyle: "italic",
    textAlign: "center",
    padding: THEME.spacing.m,
  },
  listItem: {
    width: "100%",
    paddingVertical: THEME.spacing.s,
    borderBottomWidth: 1,
  },
  friendRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 10,
  },
  friendInfo: {
    flex: 1,
  },
  inviteButton: {
    width: "auto",
    marginVertical: 0,
    paddingHorizontal: 14,
    paddingVertical: 8,
    minHeight: 40,
  },
  inviteButtonText: {
    fontWeight: "700",
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
  mapPlaceholderButton: {
    borderRadius: 16,
    overflow: "hidden",
    marginHorizontal: 10,
  },
  mapPlaceholderImage: {
    width: "100%",
    height: 160,
  },
  mapPlaceholderOverlay: {
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: "rgba(0, 0, 0, 0.30)",
    paddingHorizontal: 18,
  },
  mapPlaceholderTitle: {
    ...THEME.typography.eventTitle,
    color: "#fff",
    textAlign: "center",
  },
  mapPlaceholderSubtitle: {
    ...THEME.typography.text,
    color: "#fff",
    marginTop: 6,
    textAlign: "center",
  }
});

export default AddEvent;