import React from 'react';
import { createStackNavigator } from '@react-navigation/stack';
import UserScreen from '../screens/user/UserScreen';
import EditProfileScreen from '../screens/user/EditProfileScreen';

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
        </Stack.Navigator>
    );
};

export default ProfileStack;
