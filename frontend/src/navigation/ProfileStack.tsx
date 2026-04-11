import React from 'react';
import { createStackNavigator } from '@react-navigation/stack';
import UserScreen from '../screens/user/UserScreen';
import EditProfileScreen from '../screens/user/EditProfileScreen';
import SettingsScreen from '../screens/user/SettingsScreen';
import { useTheme } from '../contexts/ThemeContext';

const Stack = createStackNavigator();

const ProfileStack = () => {
    const { colors } = useTheme();

    return (
        <Stack.Navigator
            screenOptions={{
                headerShown: false,
                headerStyle: { backgroundColor: colors.background },
                headerTintColor: colors.text,
                headerTitleStyle: { color: colors.text },
                headerShadowVisible: false,
            }}
        >
        <Stack.Screen 
            name="UserProfile" 
            component={UserScreen}
        />
            <Stack.Screen
                name="EditProfile"
                component={EditProfileScreen}
                options={{ headerShown: true, title: "Edycja Profilu" }}
            />
            <Stack.Screen
                name="SettingsScreen"
                component={SettingsScreen}
                options={{ headerShown: true, title: "Ustawienia Konfiguracyjne" }}
            />
        </Stack.Navigator>
    );
};

export default ProfileStack;
