import React from 'react';
import { createStackNavigator } from '@react-navigation/stack';
import UserScreen from '../screens/user/UserScreen';
import EditProfileScreen from '../screens/user/EditProfileScreen';
import SettingsScreen from '../screens/user/SettingsScreen';

const Stack = createStackNavigator();

const ProfileStack = () => {
    return (
        <Stack.Navigator screenOptions={{ headerShown: false }}>
            <Stack.Screen name="UserProfile" component={UserScreen} />
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
