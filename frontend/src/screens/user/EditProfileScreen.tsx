import React, { useState } from 'react';
import { View, Text, StyleSheet, TextInput, Alert, TouchableOpacity, Image } from 'react-native';
import { useAuth } from '../../contexts/AuthContext';
import { useNavigation } from '@react-navigation/native';
import { THEME } from '../../utils/constants';
import Button from '../../components/Button';

// Tymczasowy mock avatara dopóki backend go nie obsłuży
const MOCK_AVATAR = "https://www.hollywoodreporter.com/wp-content/uploads/2011/06/drive_primary.jpg?w=1440&h=810&crop=1"; // Ryan Gosling (Wikipedia)

const EditProfileScreen = () => {
    const { user } = useAuth();
    const navigation = useNavigation();

    // Lokalne stany dla formularza
    const [bio, setBio] = useState("Status: Zdałem AUE!?@!");
    const [email, setEmail] = useState(user?.email || "");
    const [username, setUsername] = useState(user?.username || "");

    const handleSave = () => {
        // Tu wywołanie bazy
        console.log("Zapisywanie profilu:", { username, bio, email });
        Alert.alert(
            "Sukces",
            "Zaktualizowano profil (Mock)",
            [{ text: "OK", onPress: () => navigation.goBack() }]
        );
    };

    return (
        <View style={styles.container}>
            {/* Sekcja Avatara */}
            <View style={styles.avatarSection}>
                <View style={styles.avatarContainer}>
                    <Image source={{ uri: MOCK_AVATAR }} style={styles.avatar} />
                </View>
                <TouchableOpacity onPress={() => Alert.alert("Info", "Zmiana avatara udostępniona po wpięciu do API!")}>
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
    avatarContainer: {
        width: 100,
        height: 100,
        borderRadius: THEME.borderRadius.l,
        overflow: 'hidden',
        borderWidth: 1,
        borderColor: THEME.colors.lm_src_br,
        backgroundColor: THEME.colors.lm_src_br,
        marginBottom: THEME.spacing.s,
    },
    avatar: {
        width: "100%",
        height: "100%",
        resizeMode: "cover",
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
        fontWeight: '600',
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
        fontSize: 12,
        color: THEME.colors.lm_ico,
        marginBottom: THEME.spacing.s,
        marginTop: THEME.spacing.xs,
    }
});

export default EditProfileScreen;
