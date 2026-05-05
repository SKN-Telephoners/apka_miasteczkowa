import React from 'react';
import { createStackNavigator } from '@react-navigation/stack';
import UserScreen from '../screens/user/UserScreen';
import EditProfileScreen from '../screens/user/EditProfileScreen';
import SettingsScreen from '../screens/user/SettingsScreen';
import EventPreviewScreen from '../screens/event/EventPreviewScreen';
import EditEvent from '../screens/event/EditEvent';
import EventMap from '../screens/event/EventMap';
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
            options={({ route }) => {
                const isVisitedProfile = Boolean((route as any)?.params?.visitedUser);
                return {
                    headerShown: isVisitedProfile,
                    title: "Profil użytkownika",
                };
            }}
        />
            <Stack.Screen
                name="EditProfile"
                component={EditProfileScreen}
                options={{ headerShown: true, title: "Edycja Profilu" }}
            />
            <Stack.Screen
                name="SettingsScreen"
                component={SettingsScreen}
                options={{ headerShown: true, title: "Ustawienia" }}
            />
            <Stack.Screen
                name="MyEventPreview"
                component={EventPreviewScreen}
                options={{ headerShown: true, title: "Moje wydarzenie" }}
            />
            <Stack.Screen
                name="EditEvent"
                component={EditEvent}
                options={{ headerShown: true, title: "Edytuj wydarzenie" }}
            />
            <Stack.Screen
                name="EventMap"
                component={EventMap}
                options={{ headerShown: true, title: "Wybierz lokalizację" }}
            />
        </Stack.Navigator>
    );
};

export default ProfileStack;
