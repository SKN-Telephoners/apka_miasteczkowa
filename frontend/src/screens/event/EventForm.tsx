import React, { useEffect, useLayoutEffect, useMemo, useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  SafeAreaView,
  Image,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  ToastAndroid,
  TextInput,
} from "react-native";
import { useNavigation, useRoute } from "@react-navigation/native";
import * as ImagePicker from "expo-image-picker";
import * as FileSystem from "expo-file-system";
import Checkbox from "expo-checkbox";

import {
  createEvent,
  editEvent,
  inviteToEvent,
  deleteInviteToEvent,
  uploadEventPicture,
  getSentInvitesForEvent,
} from "../../services/events";
import { useTheme } from "../../contexts/ThemeContext";
import { useUser } from "../../contexts/UserContext";
import { useFriends } from "../../contexts/FriendsContext";
import DatePicker from "../../components/DateTimePicker";
import UserCard from "../../components/UserCard";
import ItemSeparator from "../../components/ItemSeparator";
import Button from "../../components/Button";
import CollapsibleSection from "../../components/CollapsibleSection";
import AppIcon from "../../components/AppIcon";
import InputField from "../../components/InputField";

import { THEME } from "../../utils/constants";
import { EventPicture } from "../../types";
import { buildEventPreview } from "../../utils/eventPreview";

interface SelectedLocationParam {
  coordinates: [number, number];
  lat: number;
  lng: number;
  timestamp: number;
}

const EventForm = () => {
  const navigation = useNavigation<any>();
  const route = useRoute<any>();
  const { colors, isDark } = useTheme();
  const { user: currentUser } = useUser();
  const { friends } = useFriends();

  const isEdit = route.name === "EditEvent" || !!route.params?.event;
  const editData = route.params?.event;

  const PREVIEW_ICON_SIZE = 22;
  const DESCRIPTION_LINE_HEIGHT = 20;
  const DESCRIPTION_MIN_HEIGHT = DESCRIPTION_LINE_HEIGHT * 5 + 20;

  const getInitialDateTime = () => {
    if (isEdit && editData.date && editData.time) {
      try {
        const [day, month, year] = editData.date.split(".").map(Number);
        const [hours, minutes] = editData.time.split(":").map(Number);
        const dateObj = new Date(year, month - 1, day);
        const timeObj = new Date(year, month - 1, day, hours, minutes);
        return { date: dateObj, time: timeObj };
      } catch (e) {
        console.error(e);
      }
    }
    const now = new Date();
    return { date: now, time: now };
  };
  const initialTimes = getInitialDateTime();

  const [title, setTitle] = useState(editData?.name || "");
  const [description, setDescription] = useState(editData?.description || "");
  const [location, setLocation] = useState(editData?.location || "");
  const [date, setDate] = useState(editData?.date || "");
  const [time, setTime] = useState(editData?.time || "");
  const [isPrivate, setIsPrivate] = useState(
    editData?.is_private || editData?.private || false,
  );
  const [eventPicture, setEventPicture] = useState<EventPicture | null>(
    editData?.pictures?.[0] ?? null,
  );
  const [eventPicturePreviewUri, setEventPicturePreviewUri] = useState<
    string | null
  >(editData?.pictures?.[0]?.url ?? null);
  const [isPictureUploading, setIsPictureUploading] = useState(false);

  const [descriptionInputHeight, setDescriptionInputHeight] = useState(
    DESCRIPTION_MIN_HEIGHT,
  );
  const [searchQuery, setSearchQuery] = useState("");
  const [invitedIds, setInvitedIds] = useState<Record<string, boolean>>({});

  const [titleError, setTitleError] = useState("");
  const [locationError, setLocationError] = useState("");

  const styles = useMemo(() => getStyles(colors, isDark), [colors, isDark]);

  useEffect(() => {
    if (isEdit) {
      const eventId = editData?.id || editData?.event_id;
      getSentInvitesForEvent(String(eventId))
        .then((ids) => {
          const map: Record<string, boolean> = {};
          ids.forEach((id) => (map[String(id)] = true));
          setInvitedIds(map);
        })
        .catch(console.error);
    }
  }, [isEdit, editData]);

  useEffect(() => {
    const selected = route.params?.selectedLocation as
      | SelectedLocationParam
      | undefined;
    if (selected?.coordinates?.length === 2) {
      setLocation(JSON.stringify(selected.coordinates));
      setLocationError("");
      navigation.setParams({ selectedLocation: undefined });
    }
  }, [route.params?.selectedLocation]);

  const previewEvent = useMemo(() => {
    return buildEventPreview({
      title,
      description,
      location,
      date,
      time,
      isPrivate,
      creatorId: String(editData?.creator_id ?? currentUser?.id ?? "preview"),
      creatorUsername: currentUser?.username || "użytkownik",
      creatorProfilePictureUrl: currentUser?.profile_picture?.url || null,
      picture: eventPicture,
      pictureUri: eventPicturePreviewUri,
      id: String(editData?.id ?? editData?.event_id ?? "preview"),
    });
  }, [
    title,
    description,
    location,
    date,
    time,
    isPrivate,
    currentUser,
    eventPicture,
    eventPicturePreviewUri,
  ]);

  useLayoutEffect(() => {
    navigation.setOptions({
      headerTitle: isEdit ? "Edytuj wydarzenie" : "Dodaj wydarzenie",
      headerRight: () => (
        <TouchableOpacity
          onPress={() =>
            navigation.navigate("EventPreview", { event: previewEvent })
          }
          style={styles.previewHeaderIcon}
          activeOpacity={0.8}
        >
          <AppIcon name="Preview" size={PREVIEW_ICON_SIZE} />
        </TouchableOpacity>
      ),
    });
  }, [navigation, previewEvent, isEdit]);

  const uploadSelectedPicture = async (asset: ImagePicker.ImagePickerAsset) => {
    if (!asset.uri) return;
    const fileInfo = await FileSystem.getInfoAsync(asset.uri);
    if (fileInfo.exists && (fileInfo.size || 0) > 15 * 1024 * 1024) {
      ToastAndroid.show("Plik jest zbyt duży", ToastAndroid.SHORT);
      return;
    }

    setEventPicturePreviewUri(asset.uri);
    setIsPictureUploading(true);
    try {
      const uploaded = await uploadEventPicture(
        asset.uri,
        asset.fileName ?? "event-picture.jpg",
      );
      setEventPicture({ ...uploaded, url: uploaded.url ?? asset.uri });
    } catch (error) {
      setEventPicturePreviewUri(null);
      ToastAndroid.show("Błąd podczas przesyłania zdjęcia", ToastAndroid.SHORT);
    } finally {
      setIsPictureUploading(false);
    }
  };

  const showPictureOptions = async () => {
    const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!permission.granted) return;
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ["images"],
      quality: 0.6,
      allowsEditing: true,
    });
    if (!result.canceled && result.assets?.[0]) {
      await uploadSelectedPicture(result.assets[0]);
    }
  };

  const handleInviteAction = async (friendId: string) => {
    const friendIdStr = String(friendId);
    const isCurrentlyInvited = !!invitedIds[friendIdStr];

    if (!isEdit) {
      setInvitedIds((prev) => ({
        ...prev,
        [friendIdStr]: !isCurrentlyInvited,
      }));
    } else {
      const eventId = String(editData?.id || editData?.event_id);
      try {
        setInvitedIds((prev) => ({
          ...prev,
          [friendIdStr]: !isCurrentlyInvited,
        }));
        if (isCurrentlyInvited) {
          await deleteInviteToEvent(eventId, friendIdStr);
        } else {
          await inviteToEvent(eventId, friendIdStr);
        }
      } catch (error) {
        setInvitedIds((prev) => ({
          ...prev,
          [friendIdStr]: isCurrentlyInvited,
        }));
        ToastAndroid.show("Błąd aktualizacji zaproszenia", ToastAndroid.SHORT);
      }
    }
  };

  const validate = () => {
    const tErr =
      title.length < 3 || title.length > 32
        ? "Tytuł musi mieć 3-32 znaków"
        : "";
    let lErr = "";
    try {
      const p = JSON.parse(location);
      if (!Array.isArray(p) || p.length !== 2) lErr = "Wybierz lokalizację";
    } catch {
      lErr = "Wybierz lokalizację na mapie";
    }

    setTitleError(tErr);
    setLocationError(lErr);

    if (tErr || lErr) return false;
    if (!date || !time) {
      ToastAndroid.show("Data i czas są wymagane", ToastAndroid.SHORT);
      return false;
    }
    return true;
  };

  const handleSubmit = async () => {
    if (isPictureUploading || !validate()) return;

    try {
      const payload = {
        name: title,
        description,
        date,
        time,
        location,
        is_private: isPrivate,
        picture: eventPicture,
      };

      if (isEdit) {
        await editEvent(editData.id || editData.event_id, payload);
        ToastAndroid.show("Zapisano zmiany", ToastAndroid.SHORT);
      } else {
        const created = await createEvent(payload);
        const toInvite = Object.entries(invitedIds)
          .filter(([_, v]) => v)
          .map(([id]) => id);
        if (created?.event_id && toInvite.length > 0) {
          await Promise.allSettled(
            toInvite.map((id) => inviteToEvent(created.event_id, id)),
          );
        }
        ToastAndroid.show("Wydarzenie utworzone", ToastAndroid.SHORT);
      }
      navigation.navigate("EventScreen");
    } catch (error) {
      ToastAndroid.show("Wystąpił problem", ToastAndroid.SHORT);
    }
  };

  const filteredFriends = useMemo(() => {
    const q = searchQuery.toLowerCase().trim();
    return q
      ? friends.filter((f) => f.username?.toLowerCase().includes(q))
      : friends;
  }, [friends, searchQuery]);

  return (
    <SafeAreaView style={styles.screen}>
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        keyboardShouldPersistTaps="handled"
      >
        <View style={styles.container}>
          <UserCard
            creatorDisplayName={currentUser?.username || "użytkownik"}
            avatarUri={currentUser?.profile_picture?.url}
            uniName={currentUser?.academy}
            majorName={currentUser?.course}
            yearOfStudy={currentUser?.year}
            showCreatedAt={false}
            showMetaIcon={false}
            showUsernameIcon={false}
          />

          <TextInput
            placeholder="Dodaj tytuł..."
            placeholderTextColor={colors.searchWord}
            style={styles.titleInput}
            value={title}
            onChangeText={setTitle}
          />
          {!!titleError && <Text style={styles.errorText}>{titleError}</Text>}

          <TouchableOpacity
            style={styles.photoButton}
            onPress={showPictureOptions}
            disabled={isPictureUploading}
          >
            {isPictureUploading ? (
              <View style={styles.photoPlaceholder}>
                <ActivityIndicator
                  size="large"
                  color={colors.transparentHighlight}
                />
              </View>
            ) : eventPicture?.url || eventPicturePreviewUri ? (
              <Image
                source={{ uri: eventPicture?.url ?? eventPicturePreviewUri! }}
                style={styles.photo}
              />
            ) : (
              <>
                <Image
                  source={
                    isDark
                      ? require("../../../assets/photo_icon_dark.jpg")
                      : require("../../../assets/photo_icon.jpg")
                  }
                  style={styles.photo}
                />
                <View style={styles.photoOverlay}>
                  <Text style={styles.photoOverlayTitle}>Dodaj zdjęcie</Text>
                </View>
              </>
            )}
          </TouchableOpacity>

          <TextInput
            placeholder="Dodaj opis..."
            placeholderTextColor={colors.searchWord}
            style={[
              styles.descriptionInput,
              { height: descriptionInputHeight },
            ]}
            multiline
            value={description}
            onChangeText={setDescription}
            onContentSizeChange={(e) =>
              setDescriptionInputHeight(
                Math.max(
                  DESCRIPTION_MIN_HEIGHT,
                  e.nativeEvent.contentSize.height,
                ),
              )
            }
          />

          <ItemSeparator />

          <Text style={styles.sectionTitle}>Lokalizacja</Text>
          <TouchableOpacity
            style={styles.mapButton}
            onPress={() =>
              navigation.navigate("EventMap", {
                returnTo: "EventForm",
                sourceRouteKey: route.key,
              })
            }
          >
            <Image
              source={require("../../../assets/map_selection.jpg")}
              style={styles.mapImage}
            />
            <View style={styles.mapOverlay}>
              <Text style={styles.mapOverlayTitle}>
                {location
                  ? "Lokalizacja wybrana"
                  : "Wybierz lokalizację na mapie"}
              </Text>
            </View>
          </TouchableOpacity>
          {!!locationError && (
            <Text style={styles.errorText}>{locationError}</Text>
          )}

          <ItemSeparator />

          <CollapsibleSection
            title="Zaproś znajomych"
            initialExpanded={false}
            style={{ padding: 10 }}
          >
            <InputField
              placeholder="Szukaj znajomych..."
              value={searchQuery}
              onChangeText={setSearchQuery}
              showSearchSpriteIcon
              showFloatingLabel={false}
              reserveErrorSpace={false}
            />
            {filteredFriends.map((friend) => (
              <View key={friend.id} style={styles.friendRow}>
                <View style={{ flex: 1 }}>
                  <UserCard
                    creatorDisplayName={friend.username}
                    avatarUri={
                      friend?.profile_picture?.url ||
                      (typeof friend?.profile_picture === "string"
                        ? friend.profile_picture
                        : undefined)
                    }
                    showCreatedAt={false}
                    avatarSize={40}
                  />
                </View>
                <Button
                  title={invitedIds[String(friend.id)] ? "Wysłano" : "Zaproś"}
                  onPress={() => handleInviteAction(friend.id)}
                  style={styles.inviteButton}
                  textStyle={styles.inviteButtonText}
                />
              </View>
            ))}
          </CollapsibleSection>

          <ItemSeparator />

          <Text style={styles.sectionTitle}>Data i czas</Text>
          <DatePicker
            onDateSelected={(d, t) => {
              setDate(d);
              setTime(t);
            }}
            initialDate={initialTimes.date}
            initialTime={initialTimes.time}
          />

          <ItemSeparator />

          <View style={styles.checkboxRow}>
            <Checkbox
              value={isPrivate}
              onValueChange={setIsPrivate}
              color={isPrivate ? colors.transparentHighlight : undefined}
            />
            <Text style={styles.checkboxLabel}>Wydarzenie prywatne</Text>
          </View>

          <Button
            onPress={handleSubmit}
            title={
              isPictureUploading
                ? "Przesyłanie..."
                : isEdit
                  ? "Zapisz zmiany"
                  : "Opublikuj"
            }
            disabled={isPictureUploading}
          />
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

const getStyles = (colors: any, isDark: boolean) =>
  StyleSheet.create({
    screen: { flex: 1, backgroundColor: colors.background },
    scrollView: { flex: 1 },
    scrollContent: { paddingBottom: 24 },
    container: { padding: 10 },
    previewHeaderIcon: { marginRight: 16, width: 22, height: 22 },
    titleInput: {
      marginVertical: 10,
      paddingVertical: 10,
      marginHorizontal: 10,
      ...THEME.typography.title,
      color: colors.text,
      borderBottomWidth: 1,
      borderColor: colors.icon,
    },
    descriptionInput: {
      padding: 10,
      marginVertical: 10,
      marginHorizontal: 10,
      ...THEME.typography.text,
      color: colors.text,
      textAlignVertical: "top",
      borderWidth: 0.5,
      borderColor: colors.icon,
      borderRadius: THEME.borderRadius.xl,
    },
    sectionTitle: {
      padding: 10,
      ...THEME.typography.eventTitle,
      color: colors.text,
    },
    photoButton: {
      marginHorizontal: 10,
      marginVertical: 10,
      borderRadius: 16,
      overflow: "hidden",
      height: 250,
    },
    photo: { width: "100%", height: "100%" },
    photoPlaceholder: {
      flex: 1,
      backgroundColor: colors.border,
      justifyContent: "center",
      alignItems: "center",
    },
    photoOverlay: {
      ...StyleSheet.absoluteFillObject,
      backgroundColor: "rgba(0,0,0,0.3)",
      justifyContent: "center",
      alignItems: "center",
    },
    photoOverlayTitle: { ...THEME.typography.eventTitle, color: "#fff" },
    mapButton: {
      marginHorizontal: 10,
      borderRadius: THEME.borderRadius.xl,
      overflow: "hidden",
      height: 160,
    },
    mapImage: { width: "100%", height: "100%" },
    mapOverlay: {
      ...StyleSheet.absoluteFillObject,
      backgroundColor: "rgba(0,0,0,0.3)",
      justifyContent: "center",
      alignItems: "center",
    },
    mapOverlayTitle: {
      ...THEME.typography.eventTitle,
      color: "#fff",
      textAlign: "center",
    },
    friendRow: {
      flexDirection: "row",
      alignItems: "center",
      paddingVertical: 8,
      borderBottomWidth: 1,
      borderColor: colors.border,
    },
    inviteButton: {
      width: "auto",
      marginVertical: 0,
      paddingHorizontal: 14,
      minHeight: 40,
    },
    inviteButtonText: { fontWeight: "700" },
    checkboxRow: {
      flexDirection: "row",
      alignItems: "center",
      padding: 10,
      marginVertical: 10,
    },
    checkboxLabel: {
      marginLeft: 10,
      ...THEME.typography.text,
      color: colors.text,
    },
    errorText: {
      color: colors.aghRed,
      fontSize: 12,
      marginLeft: 10,
      marginTop: -5,
      marginBottom: 5,
    },
  });

export default EventForm;
