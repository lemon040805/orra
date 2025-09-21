import React from 'react';
import {TextInput, StyleSheet, TextInputProps} from 'react-native';

interface CustomInputProps extends TextInputProps {
  placeholder: string;
}

const CustomInput: React.FC<CustomInputProps> = ({placeholder, style, ...props}) => {
  return (
    <TextInput
      style={[styles.input, style]}
      placeholder={placeholder}
      placeholderTextColor="#999"
      {...props}
    />
  );
};

const styles = StyleSheet.create({
  input: {
    width: '100%',
    paddingVertical: 16,
    paddingHorizontal: 16,
    borderWidth: 2,
    borderColor: '#e5e5e5',
    borderRadius: 12,
    fontSize: 16,
    marginBottom: 16,
    backgroundColor: 'white',
    fontWeight: '400',
  },
});

export default CustomInput;