import React from 'react';
import { View, TouchableOpacity, Text, StyleSheet } from 'react-native';
import { useTheme } from '../contexts/ThemeContext';
import { THEME } from '../utils/constants';

interface Props {
    onAccept: () => void;
    onDecline: () => void;
}

const NotificationActionButtons: React.FC<Props> = ({ onAccept, onDecline }) => {
    const { colors } = useTheme();

    return (
        <View style={styles.actionButtons}>
            <TouchableOpacity
                style={[styles.button, { backgroundColor: colors.highlight }]}
                onPress={onAccept}
            >
                <Text style={styles.buttonText}>Akceptuj</Text>
            </TouchableOpacity>
            <TouchableOpacity
                style={[styles.button, styles.declineButton]}
                onPress={onDecline}
            >
                <Text style={styles.buttonText}>Odrzuć</Text>
            </TouchableOpacity>
        </View>
    );
};

const styles = StyleSheet.create({
    actionButtons: {
        flexDirection: 'row',
        gap: 8,
    },
    button: {
        paddingHorizontal: 12,
        paddingVertical: 8,
        borderRadius: THEME.borderRadius.s,
    },
    declineButton: {
        backgroundColor: '#e74c3c',
    },
    buttonText: {
        color: '#FFFFFF',
        fontWeight: 'bold',
    },
});

export default NotificationActionButtons;
