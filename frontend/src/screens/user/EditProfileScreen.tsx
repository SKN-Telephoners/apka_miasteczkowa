import React, { useState } from 'react';
import { View, Text, StyleSheet, TextInput, Alert, TouchableOpacity, Image } from 'react-native';
import { useAuth } from '../../contexts/AuthContext';
import { useUser } from '../../contexts/UserContext';
import { useNavigation } from '@react-navigation/native';
import { THEME, MOCKS } from '../../utils/constants';
import Button from '../../components/Button';
import Avatar from '../../components/Avatar';

const EditProfileScreen = () => {
    const { user, updateUser } = useUser();
    const navigation = useNavigation();

    // Lokalne stany dla formularza
    const [bio, setBio] = useState(user?.bio || "");
    const [avatar, setAvatar] = useState(user?.avatar || MOCKS.AVATAR);
    const [email, setEmail] = useState(user?.email || "");
    const [username, setUsername] = useState(user?.username || "");

    const handleSave = () => {
        // Tu wywołanie bazy
        updateUser({ bio, avatar });
        console.log("Zapisywanie profilu:", { username, bio, email, avatar });
        Alert.alert(
            "Sukces",
            "Zaktualizowano profil (Mock zapisał do Contextu)",
            [{ text: "OK", onPress: () => navigation.goBack() }]
        );
    };

    return (
        <View style={styles.container}>
            {/* Sekcja Avatara */}
            <View style={styles.avatarSection}>
                <Avatar uri={avatar} size={100} style={{ marginBottom: THEME.spacing.s }} />
                <TouchableOpacity onPress={() => {
                    // MOCK: W przyszłości tu wejdzie expo-image-picker
                    const mockAvatars = [
                        "https://images.unsplash.com/photo-1599566150163-29194dcaad36?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
                        "https://images.unsplash.com/photo-1494790108377-be9c29b29330?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
                        "https://images.unsplash.com/photo-1527980965255-d3b416303d12?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
                        "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80"
                    ];
                    const randomAvatar = mockAvatars[Math.floor(Math.random() * mockAvatars.length)];
                    setAvatar(randomAvatar);
                    Alert.alert("Mock", "Wylosowano awatar! Docelowo otworzy się galeria urządzenia.");
                }}>
                    <Text style={styles.changeAvatarText}>Zmień zdjęcie</Text>
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

                <Text style={[styles.label, { marginTop: THEME.spacing.m }]}>Bio / Status</Text>
                <TextInput
                    style={[styles.input, styles.bioInput]}
                    value={bio}
                    onChangeText={setBio}
                    multiline
                    placeholder="Napisz coś o sobie..."
                    placeholderTextColor={THEME.colors.lm_srch_wrd}
                />
            </View>

            {/* Przycisk zapisu */}
            <Button title="Zapisz zmiany" onPress={handleSave} />
        </View>
    );
};

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: THEME.colors.lm_bg,
        padding: THEME.spacing.m,
    },
    avatarSection: {
        alignItems: 'center',
        marginVertical: THEME.spacing.l,
    },
    changeAvatarText: {
        ...THEME.typography.text,
        color: THEME.colors.lm_highlight,
        fontWeight: 'bold',
    },
    formSection: {
        flex: 1, // Pozwala przyciskowi odsunąć się na dół, jeśli jest mało miejsca
    },
    label: {
        ...THEME.typography.text,
        color: THEME.colors.lm_txt,
        marginBottom: THEME.spacing.xs,
    },
    input: {
        ...THEME.typography.text,
        borderWidth: 1,
        borderColor: THEME.colors.lm_src_br,
        borderRadius: THEME.borderRadius.m,
        padding: THEME.spacing.m,
        backgroundColor: THEME.colors.lm_bg,
    },
    disabledInput: {
        backgroundColor: THEME.colors.lm_src_br,
        color: THEME.colors.lm_ico,
    },
    bioInput: {
        height: 100,
        textAlignVertical: 'top', // Wyrównanie do góry na Androidzie
    },
    hint: {
        ...THEME.typography.text,
        color: THEME.colors.lm_ico,
        marginBottom: THEME.spacing.s,
        marginTop: THEME.spacing.xs,
    }
});

export default EditProfileScreen;
