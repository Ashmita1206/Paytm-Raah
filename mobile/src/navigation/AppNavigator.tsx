import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { HomeScreen } from '../screens/HomeScreen';
import { ScannerScreen } from '../screens/ScannerScreen';
import { PaymentResultScreen } from '../screens/PaymentResultScreen';
import { PaymentRescueScreen } from '../screens/PaymentRescueScreen';
import { PulseOperationsScreen } from '../screens/PulseOperationsScreen';

export type RootStackParamList = {
  Home: undefined;
  Scanner: undefined;
  PaymentResult: {
    transactionId: string;
    amount?: number;
    merchantName?: string;
    status?: string;
  };
  PaymentRescue: {
    transactionId: string;
  };
  PulseOperations: undefined;
};

const Stack = createNativeStackNavigator<RootStackParamList>();

export const AppNavigator: React.FC = () => {
  return (
    <NavigationContainer>
      <Stack.Navigator
        initialRouteName="Home"
        screenOptions={{
          headerShown: false,
          animation: 'slide_from_right',
        }}
      >
        <Stack.Screen name="Home" component={HomeScreen} />
        <Stack.Screen name="Scanner" component={ScannerScreen} />
        <Stack.Screen name="PaymentResult" component={PaymentResultScreen} />
        <Stack.Screen name="PaymentRescue" component={PaymentRescueScreen} />
        <Stack.Screen name="PulseOperations" component={PulseOperationsScreen} />
      </Stack.Navigator>
    </NavigationContainer>
  );
};
