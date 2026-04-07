import React, { useState, useMemo } from 'react';
import { View, Text, StyleSheet, TextInput, Alert, TouchableOpacity, Image, ScrollView } from 'react-native';
import { useAuth } from '../../contexts/AuthContext';
import { useUser } from '../../contexts/UserContext';
import { useNavigation } from '@react-navigation/native';
import { useTheme } from '../../contexts/ThemeContext';
import { THEME, MOCKS, ACADEMIES } from '../../utils/constants';
import Button from '../../components/Button';
import { userService } from '../../services/api';
import Avatar from '../../components/Avatar';
import AppIcon from '../../components/AppIcon';

const EditProfileScreen = () => {
    const { user, updateUser } = useUser();
    const navigation = useNavigation();
    const { colors } = useTheme();

    const styles = useMemo(() => getStyles(colors), [colors]);

    // Lokalne stany dla formularza
    const [description, setDescription] = useState(user?.description || "");
    const [academy, setAcademy] = useState(user?.academy || "");
    const [isDropdownOpen, setIsDropdownOpen] = useState(false);

    const avatar = user?.profile_picture?.url || MOCKS.AVATAR; // read-only
    const email = user?.email || ""; // read-only
    const username = user?.username || ""; // read-only
    const [isSaving, setIsSaving] = useState(false);

    const handleSave = async () => {
        setIsSaving(true);
        try {
            await userService.updateProfile({ 
                description, 
                academy: academy === "" ? null : academy 
            });
            updateUser({ description, academy });
            Alert.alert("Sukces", "Zaktualizowano profil", [{ text: "OK", onPress: () => navigation.goBack() }]);
        } catch (error) {
            Alert.alert("Błąd", "Nie udało się zapisać zmian");
        } finally {
            setIsSaving(false);
        }
    };

    return (
        <View style={styles.container}>
            {/* Sekcja Avatara */}
            <View style={styles.avatarSection}>
                <Avatar uri={avatar} size={100} style={{ marginBottom: THEME.spacing.s }} />
                <TouchableOpacity onPress={() => Alert.alert("Zablokowane", "Dodawanie zdjęcia będzie dostępne wkrótce.")}>
                    <Text style={[styles.changeAvatarText, { color: colors.icon }]}>Zmień zdjęcie (Zablokowane)</Text>
                </TouchableOpacity>
            </View>

            {/* Sekcja Formularza */}
            <View style={styles.formSection}>
                <Text style={styles.label}>Nazwa użytkownika</Text>
                <TextInput
                    style={[styles.input, styles.disabledInput]}
                    value={username}
                    editable={false}
                />
                <Text style={styles.hint}>Tylko do odczytu</Text>

                <Text style={styles.label}>Email</Text>
                <TextInput
                    style={[styles.input, styles.disabledInput]}
                    value={email}
                    editable={false}
                />

                <Text style={[styles.label, { marginTop: THEME.spacing.m }]}>Uczelnia</Text>
                <View style={styles.dropdownContainer}>
                    <TouchableOpacity
                        style={styles.dropdownButton}
                        onPress={() => setIsDropdownOpen(!isDropdownOpen)}
                    >
                        <Text style={[styles.input, styles.dropdownInputText]}>
                            {academy || "Wybierz uczelnię"}
                        </Text>
                        <AppIcon name="ArrowDown" size={24} />
                    </TouchableOpacity>

                    {isDropdownOpen && (
                        <View style={styles.dropdownList}>
                            <ScrollView nestedScrollEnabled style={{ maxHeight: 150 }}>
                                {ACADEMIES.map((acc) => (
                                    <TouchableOpacity
                                        key={acc}
                                        style={styles.dropdownItem}
                                        onPress={() => {
                                            setAcademy(acc);
                                            setIsDropdownOpen(false);
                                        }}
                                    >
                                        <Text style={styles.dropdownItemText}>{acc}</Text>
                                    </TouchableOpacity>
                                ))}
                            </ScrollView>
                        </View>
                    )}
                </View>

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
        </View>
    );
};

const getStyles = (colors: typeof THEME.colors.light) => StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: colors.background,
        padding: THEME.spacing.m,
    },
    avatarSection: {
        alignItems: 'center',
        marginVertical: THEME.spacing.l,
    },
    changeAvatarText: {
        ...THEME.typography.text,
        color: colors.highlight,
        fontWeight: 'bold',
    },
    formSection: {
        flex: 1, // Pozwala przyciskowi odsunąć się na dół, jeśli jest mało miejsca
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
    },
    dropdownContainer: {
        position: 'relative',
        zIndex: 10,
    },
    dropdownButton: {
        flexDirection: 'row',
        alignItems: 'center',
        borderWidth: 1,
        borderColor: colors.border,
        borderRadius: THEME.borderRadius.m,
        backgroundColor: colors.background,
        paddingRight: THEME.spacing.s,
    },
    dropdownInputText: {
        flex: 1,
        borderWidth: 0,
        backgroundColor: 'transparent',
    },
    dropdownList: {
        marginTop: THEME.spacing.xs,
        backgroundColor: colors.background,
        borderWidth: 1,
        borderColor: colors.border,
        borderRadius: THEME.borderRadius.m,
        overflow: 'hidden',
    },
    dropdownItem: {
        padding: THEME.spacing.m,
        borderBottomWidth: 1,
        borderBottomColor: colors.border,
    },
    dropdownItemText: {
        ...THEME.typography.text,
        color: colors.text,
    }
});

export default EditProfileScreen;
