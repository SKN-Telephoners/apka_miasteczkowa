import React, { useState } from 'react';
import { View, Text, StyleSheet, TextInput, ScrollView, Button, Alert, TouchableOpacity } from 'react-native';
import { useAuth } from '../../contexts/AuthContext';
import { useNavigation } from '@react-navigation/native';

const EditProfileScreen = () => {
    const { user } = useAuth();
    const navigation = useNavigation();

    // Lokalne stany dla formularza
    // W przyszłości te wartości początkowe powinny pochodzić z UserContext / API
    const [bio, setBio] = useState("Status: Dostępny w miasteczku!");
    const [email, setEmail] = useState(user?.email || "");
    const [username, setUsername] = useState(user?.username || "");

    // Mock zapisu
    const handleSave = () => {
        // Tu powinno być wywołanie API: await updateUserProfile({ bio, email ... })
        console.log("Zapisywanie profilu:", { username, bio, email });

        Alert.alert(
            "Sukces",
            "Zaktualizowano profil (Mock)",
            [
                { text: "OK", onPress: () => navigation.goBack() }
            ]
        );
    };

    return (
        <ScrollView style={styles.container}>
            <View style={styles.avatarSection}>
                <View style={styles.avatarPlaceholder}>
                    <Text style={styles.avatarEmoji}>👤</Text>
                </View>
                <TouchableOpacity onPress={() => Alert.alert("Info", "Zmiana avatara dostępna wkrótce!")}>
                    <Text style={styles.changeAvatarText}>Zmień zdjęcie</Text>
                </TouchableOpacity>
            </View>

            <View style={styles.formSection}>
                <Text style={styles.label}>Nazwa użytkownika</Text>
                <TextInput
                    style={styles.input}
                    value={username}
                    onChangeText={setUsername}
                    editable={false}
                />
                <Text style={styles.hint}>Nazwa użytkownika jest stała.</Text>

                <Text style={styles.label}>Email (Tylko do odczytu)</Text>
                <TextInput
                    style={[styles.input, styles.disabledInput]}
                    value={email}
                    editable={false}
                />

                <Text style={styles.label}>Bio / Status</Text>
                <TextInput
                    style={[styles.input, styles.bioInput]}
                    value={bio}
                    onChangeText={setBio}
                    multiline
                    placeholder="Napisz coś o sobie..."
                />
            </View>

            <View style={styles.buttonSection}>
                <Button title="Zapisz zmiany" onPress={handleSave} />
            </View>
        </ScrollView>
    );
};

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#fff',
        padding: 20,
    },
    avatarSection: {
        alignItems: 'center',
        marginVertical: 20,
    },
    avatarPlaceholder: {
        width: 100,
        height: 100,
        borderRadius: 50,
        backgroundColor: '#f0f0f0',
        justifyContent: 'center',
        alignItems: 'center',
        marginBottom: 10,
    },
    avatarEmoji: {
        fontSize: 50,
    },
    changeAvatarText: {
        color: '#007AFF',
        fontSize: 16,
    },
    formSection: {
        marginBottom: 30,
    },
    label: {
        fontSize: 16,
        fontWeight: '600',
        marginBottom: 5,
        color: '#333',
    },
    input: {
        borderWidth: 1,
        borderColor: '#ddd',
        borderRadius: 8,
        padding: 12,
        fontSize: 16,
        marginBottom: 5,
        backgroundColor: '#fafafa',
    },
    disabledInput: {
        backgroundColor: '#eee',
        color: '#888',
    },
    bioInput: {
        height: 100,
        textAlignVertical: 'top', // Dla Androida
    },
    hint: {
        fontSize: 12,
        color: '#888',
        marginBottom: 15,
    },
    buttonSection: {
        marginBottom: 40,
    }
});

export default EditProfileScreen;
