import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

const EditProfileScreen = () => {
    return (
        <View style={styles.container}>
            <Text style={styles.text}>Edycja profilu - Placeholder</Text>
            <Text style={styles.subText}>Tu znajdzie się formularz edycji danych użytkownika.</Text>
        </View>
    );
};

const styles = StyleSheet.create({
    container: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
        backgroundColor: '#fff',
        padding: 20,
    },
    text: {
        fontSize: 24,
        fontWeight: 'bold',
        marginBottom: 10,
    },
    subText: {
        fontSize: 16,
        color: '#666',
        textAlign: 'center',
    },
});

export default EditProfileScreen;
