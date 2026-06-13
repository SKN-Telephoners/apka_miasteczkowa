import React, { useState, useMemo } from 'react';
import { View, Text, StyleSheet, TextInput, ToastAndroid, TouchableOpacity, Image, ScrollView } from 'react-native';
import { useUser } from '../../contexts/UserContext';
import { useNavigation } from '@react-navigation/native';
import { useTheme } from '../../contexts/ThemeContext';
import { THEME, ACADEMIES } from '../../utils/constants';
import Button from '../../components/Button';
import CustomDropdown from '../../components/CustomDropdown';
import { userService } from '../../services/api';
import AppIcon from '../../components/AppIcon';
import * as ImagePicker from 'expo-image-picker';
import * as FileSystem from 'expo-file-system';
import { uploadEventPicture } from '../../services/events';
import { COURSES } from '../../utils/courses';
import { FACULTIES } from '../../utils/faculties';

const YEARS = [1, 2, 3, 4, 5, 6];

const EditProfileScreen = () => {
    const { user, updateUserProfile } = useUser();
    const navigation = useNavigation();
    const { colors } = useTheme();

    const styles = useMemo(() => getStyles(colors), [colors]);

    // Lokalne stany dla formularza
    const [username, setUsername] = useState(user?.username || "");
    const [email, setEmail] = useState(user?.email || "");
    const [description, setDescription] = useState(user?.description || "");
    const [academy, setAcademy] = useState(user?.academy || "");
    const [faculty, setFaculty] = useState(user?.faculty || "");
    const [course, setCourse] = useState(user?.course || "");
    const [year, setYear] = useState<number | null>(user?.year || null);
    const [profilePicture, setProfilePicture] = useState<{ cloud_id: string; url?: string } | null>(user?.profile_picture || null);
    const [profilePicturePreviewUri, setProfilePicturePreviewUri] = useState<string | null>(null);
    const [isPictureUploading, setIsPictureUploading] = useState(false);

    const avatarUri = profilePicturePreviewUri || profilePicture?.url || user?.profile_picture?.url || null;
    const [isSaving, setIsSaving] = useState(false);

    const isEmailChanged = email !== user?.email;

    const handleEmailRequest = async () => {
        try {
            await userService.changeEmail(email);
            ToastAndroid.show("Operacja zakończona pomyślnie.", ToastAndroid.SHORT);
        } catch (error) {
            ToastAndroid.show("Wystąpił problem. Spróbuj ponownie.", ToastAndroid.SHORT);
        }
    };

    const uploadSelectedPicture = async (asset: ImagePicker.ImagePickerAsset) => {
        if (!asset.uri) {
            ToastAndroid.show("Wystąpił problem. Spróbuj ponownie.", ToastAndroid.SHORT);
            return;
        }

        const fileInfo = await FileSystem.getInfoAsync(asset.uri);
        const maxBytes = 15 * 1024 * 1024;
        if (fileInfo.exists && typeof fileInfo.size === "number" && fileInfo.size > maxBytes) {
            ToastAndroid.show("Wystąpił problem. Spróbuj ponownie.", ToastAndroid.SHORT);
            return;
        }

        setProfilePicturePreviewUri(asset.uri);
        setIsPictureUploading(true);

        try {
            const uploadedPicture = await uploadEventPicture(asset.uri, asset.fileName ?? "profile-picture.jpg");
            setProfilePicture({
                cloud_id: uploadedPicture.cloud_id,
                url: uploadedPicture.url ?? asset.uri,
            });
        } catch (error: any) {
            setProfilePicturePreviewUri(null);
            ToastAndroid.show("Wystąpił problem. Spróbuj ponownie.", ToastAndroid.SHORT);
        } finally {
            setIsPictureUploading(false);
        }
    };

    const takePhoto = async () => {
        const permission = await ImagePicker.requestCameraPermissionsAsync();
        if (!permission.granted) {
            ToastAndroid.show("Wystąpił problem. Spróbuj ponownie.", ToastAndroid.SHORT);
            return;
        }

        const result = await ImagePicker.launchCameraAsync({
            mediaTypes: ["images"],
            quality: 0.7,
            allowsEditing: true,
            aspect: [1, 1],
        });

        if (!result.canceled && result.assets?.[0]) {
            await uploadSelectedPicture(result.assets[0]);
        }
    };

    const pickFromDevice = async () => {
        const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
        if (!permission.granted) {
            ToastAndroid.show("Wystąpił problem. Spróbuj ponownie.", ToastAndroid.SHORT);
            return;
        }

        const result = await ImagePicker.launchImageLibraryAsync({
            mediaTypes: ["images"],
            quality: 0.7,
            allowsEditing: true,
            aspect: [1, 1],
        });

        if (!result.canceled && result.assets?.[0]) {
            await uploadSelectedPicture(result.assets[0]);
        }
    };

    const showPictureOptions = () => {
        void pickFromDevice();
    };

    const handleSave = async () => {
        setIsSaving(true);
        try {
            await updateUserProfile({
                username,
                description,
                academy: academy === "" ? null : academy,
                faculty: faculty === "" ? null : faculty,
                course: course === "" ? null : course,
                year: year,
                profile_picture: profilePicture ? { cloud_id: profilePicture.cloud_id } : null,
            });
            ToastAndroid.show("Operacja zakończona pomyślnie.", ToastAndroid.SHORT);
            navigation.goBack();
        } catch (error) {
            ToastAndroid.show("Wystąpił problem. Spróbuj ponownie.", ToastAndroid.SHORT);
        } finally {
            setIsSaving(false);
        }
    };

    return (
        <ScrollView
            style={styles.container}
            contentContainerStyle={styles.scrollContent}
            keyboardShouldPersistTaps="handled"
            showsVerticalScrollIndicator={false}
        >
            <View style={styles.avatarSection}>
                <Image
                    source={
                        avatarUri
                            ? { uri: avatarUri }
                            : require('../../../assets/portrait_Placeholder.png')
                    }
                    style={styles.avatarImage}
                />
                <TouchableOpacity onPress={showPictureOptions} disabled={isPictureUploading}>
                    <Text style={[styles.changeAvatarText, { color: colors.icon }]}>
                        {isPictureUploading ? "Przesyłanie zdjęcia..." : "Zmień zdjęcie"}
                    </Text>
                </TouchableOpacity>
            </View>

            <View style={styles.formSection}>
                <Text style={styles.label}>Nazwa użytkownika</Text>
                <TextInput
                    style={styles.input}
                    value={username}
                    onChangeText={setUsername}
                />

                <Text style={[styles.label, { marginTop: THEME.spacing.m }]}>Email</Text>
                <TextInput
                    style={styles.input}
                    value={email}
                    onChangeText={setEmail}
                    keyboardType="email-address"
                    autoCapitalize="none"
                />
                {isEmailChanged && (
                    <TouchableOpacity onPress={handleEmailRequest} style={{ marginTop: THEME.spacing.xs, alignSelf: 'flex-start' }}>
                        <Text style={{ color: colors.highlight, fontWeight: 'bold' }}>
                            Zatwierdź zmianę e-maila
                        </Text>
                    </TouchableOpacity>
                )}

                <Text style={[styles.label, { marginTop: THEME.spacing.m }]}>Uczelnia</Text>
                <CustomDropdown
                    data={ACADEMIES as unknown as string[]}
                    selectedValue={academy}
                    onSelect={(val) => {
                        setAcademy(String(val));
                        if (val !== "AGH") {
                            setFaculty("");
                            setCourse("");
                            setYear(null);
                        }
                    }}
                    placeholder="Wybierz uczelnię"
                />

                {academy === "AGH" && (
                    <>
                        <Text style={[styles.label, { marginTop: THEME.spacing.m }]}>Wydział</Text>
                        <CustomDropdown
                            data={FACULTIES}
                            selectedValue={faculty}
                            onSelect={(val) => setFaculty(String(val))}
                            placeholder="Wybierz wydział"
                            searchable
                        />

                        <Text style={[styles.label, { marginTop: THEME.spacing.m }]}>Rok studiów</Text>
                        <CustomDropdown
                            data={YEARS}
                            selectedValue={year}
                            onSelect={(val) => setYear(Number(val))}
                            placeholder="Wybierz rok studiów"
                        />

                        <Text style={[styles.label, { marginTop: THEME.spacing.m }]}>Kierunek</Text>
                        <CustomDropdown
                            data={COURSES}
                            selectedValue={course}
                            onSelect={(val) => setCourse(String(val))}
                            placeholder="Wybierz kierunek"
                            searchable
                        />
                    </>
                )}

                <Text style={[styles.label, { marginTop: THEME.spacing.m }]}>Opis / Bio</Text>
                <TextInput
                    style={[styles.input, styles.bioInput]}
                    value={description}
                    onChangeText={setDescription}
                    multiline
                    placeholder="Napisz coś o sobie..."
                    placeholderTextColor={colors.searchWord}
                />
            </View>

            {/* Przycisk zapisu */}
            <Button title={isSaving ? "Zapisywanie..." : "Zapisz zmiany"} onPress={handleSave} disabled={isSaving} />
        </ScrollView>
    );
};

const getStyles = (colors: typeof THEME.colors.light) => StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: colors.background,
    },
    scrollContent: {
        padding: THEME.spacing.m,
        paddingBottom: THEME.spacing.xl,
    },
    avatarSection: {
        alignItems: 'center',
        marginVertical: THEME.spacing.l,
    },
    avatarImage: {
        width: 100,
        height: 100,
        borderRadius: 50,
        marginBottom: THEME.spacing.s,
        borderWidth: 2,
        borderColor: colors.text,
        backgroundColor: colors.border,
    },
    changeAvatarText: {
        ...THEME.typography.text,
        color: colors.highlight,
        fontWeight: 'bold',
    },
    formSection: {
        marginBottom: THEME.spacing.l,
    },
    label: {
        ...THEME.typography.text,
        color: colors.text,
        marginBottom: THEME.spacing.xs,
    },
    input: {
        ...THEME.typography.text,
        borderWidth: 1,
        borderColor: colors.border,
        borderRadius: THEME.borderRadius.m,
        padding: THEME.spacing.m,
        backgroundColor: colors.background,
        color: colors.text,
    },
    disabledInput: {
        backgroundColor: colors.border,
        color: colors.icon,
    },
    bioInput: {
        height: 100,
        textAlignVertical: 'top', // Wyrównanie do góry na Androidzie
    },
    hint: {
        ...THEME.typography.text,
        color: colors.icon,
        marginBottom: THEME.spacing.s,
        marginTop: THEME.spacing.xs,
    }
});

export default EditProfileScreen;
